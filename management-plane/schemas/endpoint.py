from typing import Optional
from pydantic import BaseModel


class EndpointCreate(BaseModel):
    hostname: str
    ip: Optional[str] = None
    os: Optional[str] = None
    status: Optional[str] = "active"
    tags: Optional[str] = None


class EndpointUpdate(BaseModel):
    hostname: Optional[str] = None
    ip: Optional[str] = None
    os: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[str] = None


class EndpointOut(BaseModel):
    id: str
    hostname: str
    ip: Optional[str]
    os: Optional[str]
    status: str
    tags: Optional[str]

    class Config:
        from_attributes = True
