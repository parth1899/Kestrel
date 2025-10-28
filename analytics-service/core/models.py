from pydantic import BaseModel
from typing import List, Dict, Any
from uuid import UUID

class EnrichedEvent(BaseModel):
    event_id: UUID
    agent_id: str
    event_type: str
    payload: Dict[str, Any]
    enrichment: Dict[str, Any]
    timestamp: str

class Alert(BaseModel):
    id: UUID
    event_id: UUID
    agent_id: str
    event_type: str
    score: float
    severity: str
    source: str
    details: Dict[str, Any]