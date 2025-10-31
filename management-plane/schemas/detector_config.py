from typing import Optional
from pydantic import BaseModel


class DetectorConfigCreate(BaseModel):
    detector_name: str
    params: str = '{}'
    version: Optional[str] = None


class DetectorConfigUpdate(BaseModel):
    detector_name: Optional[str] = None
    params: Optional[str] = None
    version: Optional[str] = None


class DetectorConfigOut(BaseModel):
    id: str
    detector_name: str
    params: str
    version: Optional[str]

    class Config:
        from_attributes = True
