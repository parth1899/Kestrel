from typing import Optional
from pydantic import BaseModel


class RuleCreate(BaseModel):
    name: str
    type: str
    definition: str
    enabled: bool = True
    policy_id: Optional[str] = None


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    definition: Optional[str] = None
    enabled: Optional[bool] = None
    policy_id: Optional[str] = None


class RuleOut(BaseModel):
    id: str
    name: str
    type: str
    definition: str
    enabled: bool
    policy_id: Optional[str]

    class Config:
        from_attributes = True
