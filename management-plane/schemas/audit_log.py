from typing import Optional
from pydantic import BaseModel


class AuditLogCreate(BaseModel):
    actor: Optional[str] = None
    action: str
    details: Optional[str] = None


class AuditLogOut(BaseModel):
    id: str
    actor: Optional[str]
    action: str
    details: Optional[str]

    class Config:
        from_attributes = True
