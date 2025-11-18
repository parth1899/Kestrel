from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from pathlib import Path
import json

from ..core.parser import parse_playbook_yaml
from ..core.executor import execute_playbook, get_execution_cached
from ..utils.config import load_config

router = APIRouter(prefix="/executions", tags=["executions"])


class RunRequest(BaseModel):
    playbook_id: str
    alert: Dict[str, Any]


@router.post("/run")
async def run(req: RunRequest):
    cfg = load_config()
    file = None
    for base in (cfg["data"]["playbooks_static"], cfg["data"]["playbooks_generated"]):
        cand = Path(base) / f"{req.playbook_id}.yaml"
        if cand.exists():
            file = cand
            break
    if not file:
        raise HTTPException(status_code=404, detail="Playbook not found")
    pb = parse_playbook_yaml(file)
    result = await execute_playbook(pb, req.alert)
    return result.model_dump()


@router.get("/{execution_id}")
async def get_execution(execution_id: str):
    cfg = load_config()
    if not cfg["execution"].get("persist", True):
        cached = get_execution_cached(execution_id)
        if not cached:
            raise HTTPException(status_code=404, detail="Execution not found (non-persistent mode)")
        return cached
    f = Path(cfg["data"]["executions"]) / f"{execution_id}.json"
    if not f.exists():
        raise HTTPException(status_code=404, detail="Execution not found")
    with open(f, "r", encoding="utf-8") as fp:
        return json.load(fp)
