from typing import Any, Dict, Optional
from pydantic import BaseModel


class AlertOut(BaseModel):
    id: str
    event_id: str
    agent_id: str
    event_type: str
    score: float
    severity: str
    source: str
    details: Dict[str, Any]
    timestamp: str
