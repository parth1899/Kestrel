from __future__ import annotations
import asyncio
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple
from pydantic import BaseModel

from .parser import Playbook, Step
from .evaluator import Preconditions
from ..actions.registry import get_action, get_rollback
from ..utils.logger import logger, audit
from ..utils.config import load_config
from ..utils.redis_client import get_redis, acquire_lock, check_and_set_cooldown

# Orchestrates playbook execution with sequential steps and rollback support.

class ExecutionResult(BaseModel):
    id: str
    playbook_id: str
    success: bool
    steps: List[Dict[str, Any]]
    rolled_back: bool


# In-memory store for executions when persistence disabled
_INMEM_EXECUTIONS: Dict[str, Dict[str, Any]] = {}


async def _run_steps(steps: List[Step]) -> Tuple[bool, List[Dict[str, Any]]]:
    results: List[Dict[str, Any]] = []
    from ..actions.registry import _is_admin_windows  # local import to avoid circular
    cfg = load_config()
    allow_isolate = cfg.get("execution", {}).get("allow_isolate_host", False)
    for s in steps:
        # Skip isolate_host if not allowed or not admin (prevent early failure blocking other steps)
        if s.action == "isolate_host" and (not allow_isolate or not _is_admin_windows()):
            results.append({"step": s.name, "action": s.action, "status": "skipped", "reason": "not_allowed_or_not_admin"})
            audit("step_skipped", {"step": s.name, "action": s.action, "reason": "not_allowed_or_not_admin"})
            continue
        act = get_action(s.action)
        try:
            out = await act(s.params)
            results.append({"step": s.name, "action": s.action, "status": "ok", "output": out})
            audit("step_executed", {"step": s.name, "action": s.action, "output": out})
        except Exception as e:
            results.append({"step": s.name, "action": s.action, "status": "error", "error": str(e)})
            audit("step_error", {"step": s.name, "action": s.action, "error": str(e)})
            if s.on_error == "continue":
                continue
            return False, results
    return True, results


async def _run_rollback(steps: List[Step]) -> List[Dict[str, Any]]:
    # Execute reverse order using registered rollbacks when available; else call same action if safe.
    out: List[Dict[str, Any]] = []
    for s in reversed(steps):
        rb = get_rollback(s.action)
        if rb is None:
            out.append({"step": s.name, "action": s.action, "status": "skipped", "reason": "no_rollback"})
            continue
        try:
            r = await rb(s.params)
            out.append({"step": s.name, "action": s.action, "status": "ok", "output": r})
            audit("rollback_step", {"step": s.name, "action": s.action, "output": r})
        except Exception as e:
            out.append({"step": s.name, "action": s.action, "status": "error", "error": str(e)})
            audit("rollback_error", {"step": s.name, "action": s.action, "error": str(e)})
    return out


async def execute_playbook(pb: Playbook, alert: Dict[str, Any]) -> ExecutionResult:
    cfg = load_config()
    # Cooldown gate based on event_type/severity to avoid thrash
    r = get_redis(cfg["redis"]["url"])
    cooldown_enabled = cfg["redis"].get("cooldown_enabled", True)
    cooldown_ttl = cfg["redis"].get("cooldown_ttl", 300)
    if cooldown_enabled and cooldown_ttl > 0:
        cooldown_key = f"{alert.get('event_type','unknown')}:{alert.get('severity','')}:cooldown"
        if not await check_and_set_cooldown(r, cooldown_key, cooldown_ttl):
            raise RuntimeError("Under cooldown")

    # Execution lock per agent/event to avoid concurrent conflicting actions
    lock_key = f"exec:{alert.get('agent_id','na')}:{alert.get('event_id','na')}"
    async with acquire_lock(r, lock_key, cfg["redis"]["lock_ttl"]) as locked:
        if not locked:
            raise RuntimeError("Another execution in progress")

        if not Preconditions.evaluate(pb.preconditions, {"alert": alert}):
            raise RuntimeError("Preconditions not met")

        ex_id = str(uuid.uuid4())
        success = False
        steps_out: List[Dict[str, Any]] = []
        rolled_back = False
        try:
            audit("execution_started", {"id": ex_id, "playbook_id": pb.id})
            success, steps_out = await _run_steps(pb.steps)
            if not success:
                rb_out = await _run_rollback(pb.steps if not pb.rollback else pb.rollback)
                steps_out.extend([{"rollback": rb} for rb in rb_out])
                rolled_back = True
            return await _persist_result(ex_id, pb.id, success, steps_out, rolled_back)
        finally:
            pass


async def _persist_result(ex_id: str, pb_id: str, success: bool, steps: List[Dict[str, Any]], rolled_back: bool) -> ExecutionResult:
    cfg = load_config()
    data = {
        "id": ex_id,
        "playbook_id": pb_id,
        "success": success,
        "steps": steps,
        "rolled_back": rolled_back,
    }
    if cfg["execution"].get("persist", True):
        Path(cfg["data"]["executions"]).mkdir(parents=True, exist_ok=True)
        file = Path(cfg["data"]["executions"]) / f"{ex_id}.json"
        import json
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        # store in memory for duration of process
        _INMEM_EXECUTIONS[ex_id] = data
    audit("execution_completed", {"id": ex_id, "playbook_id": pb_id, "success": success})
    return ExecutionResult(**data)


def get_execution_cached(ex_id: str) -> Dict[str, Any] | None:
    return _INMEM_EXECUTIONS.get(ex_id)
