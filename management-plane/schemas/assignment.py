from typing import Optional
from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    endpoint_id: str
    policy_id: str
    status: Optional[str] = "applied"


class AssignmentUpdate(BaseModel):
    status: Optional[str] = None


class AssignmentOut(BaseModel):
    id: str
    endpoint_id: str
    policy_id: str
    status: str

    class Config:
        from_attributes = True
