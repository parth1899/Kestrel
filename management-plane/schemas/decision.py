from typing import Any, Dict, Optional
from pydantic import BaseModel


class DecisionOut(BaseModel):
    id: str
    alert_id: str
    agent_id: str
    event_type: str
    severity: str
    score: float
    recommended_action: str
    priority: float
    rationale: Optional[Dict[str, Any]]
    status: str
    created_at: Optional[str]
    updated_at: Optional[str]
