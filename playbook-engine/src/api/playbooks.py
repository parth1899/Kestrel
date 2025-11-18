from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
from pathlib import Path

from ..utils.logger import audit
from ..utils.config import load_config
from ..genai.generator import generate_playbook, find_existing_playbook
from ..core.parser import parse_playbook_yaml
from ..core.executor import execute_playbook

router = APIRouter(prefix="/playbooks", tags=["playbooks"])


class AlertIn(BaseModel):
    event_id: Optional[str] = None
    agent_id: Optional[str] = None
    event_type: str
    severity: str
    details: Dict[str, Any] = {}


@router.post("/generate")
async def generate(alert: AlertIn):
    existing = find_existing_playbook(alert.model_dump())
    if existing:
        return {"status": "exists", "path": str(existing)}
    path = await generate_playbook(alert.model_dump())
    return {"status": "generated", "path": str(path)}


@router.post("/generate-and-run")
async def generate_and_run(alert: AlertIn):
    """Convenience endpoint: generate a playbook for the alert (or reuse existing),
    then execute it immediately and return the execution result along with the YAML path.
    """
    alert_dict = alert.model_dump()
    path = find_existing_playbook(alert_dict)
    status = "exists" if path else "generated"
    if not path:
        path = await generate_playbook(alert_dict)
    pb = parse_playbook_yaml(Path(path))
    result = await execute_playbook(pb, alert_dict)
    return {
        "status": status,
        "path": str(path),
        "playbook_id": pb.id,
        "result": result.model_dump(),
    }


@router.get("/{playbook_id}")
async def get_playbook(playbook_id: str):
    cfg = load_config()
    for base in (cfg["data"]["playbooks_static"], cfg["data"]["playbooks_generated"]):
        cand = Path(base) / f"{playbook_id}.yaml"
        if cand.exists():
            pb = parse_playbook_yaml(cand)
            return pb.model_dump()
    raise HTTPException(status_code=404, detail="Playbook not found")
