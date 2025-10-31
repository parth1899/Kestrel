from typing import Optional
from pydantic import BaseModel


class PolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    enabled: bool = True


class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class PolicyOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    enabled: bool

    class Config:
        from_attributes = True
