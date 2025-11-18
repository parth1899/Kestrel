from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field, ValidationError
from ..utils.config import load_actions_schema

# Pydantic models define the playbook schema.

class Step(BaseModel):
    name: str = Field(..., description="Human-friendly name")
    action: str = Field(..., description="Action key registered in actions.yaml/registry")
    params: Dict[str, Any] = Field(default_factory=dict)
    on_error: str = Field(default="stop")  # stop|continue|rollback

class Playbook(BaseModel):
    id: str
    version: str = "1.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)  # event_type, severity, etc.
    preconditions: List[Dict[str, Any]] = Field(default_factory=list)
    steps: List[Step] = Field(default_factory=list)
    rollback: List[Step] = Field(default_factory=list)


class PlaybookValidationError(Exception):
    pass


def _validate_against_actions_schema(pb: Playbook) -> None:
    # Verify each step exists in schema and required params are present
    schema = load_actions_schema()
    actions = (schema.get("actions") or {})
    for s in list(pb.steps) + list(pb.rollback):
        if s.action not in actions:
            raise PlaybookValidationError(f"Unknown action: {s.action}")
        required = actions[s.action].get("params", [])
        missing = [p for p in required if p not in s.params]
        if missing:
            raise PlaybookValidationError(f"Action {s.action} missing params: {missing}")


def parse_playbook_yaml(path: Path | str) -> Playbook:
    # Parse YAML file to Playbook and validate.
    p = Path(path)
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    try:
        pb = Playbook(**data)
    except ValidationError as e:
        raise PlaybookValidationError(str(e))
    _validate_against_actions_schema(pb)
    return pb


def parse_playbook_text(text: str) -> Playbook:
    data = yaml.safe_load(text) or {}
    try:
        pb = Playbook(**data)
    except ValidationError as e:
        raise PlaybookValidationError(str(e))
    _validate_against_actions_schema(pb)
    return pb
