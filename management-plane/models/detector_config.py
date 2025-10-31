from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
import uuid

from .base import Base


class DetectorConfig(Base):
    __tablename__ = "detector_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    detector_name = Column(String, nullable=False)  # e.g., rule_based, behavioral, anomaly
    params = Column(Text, nullable=False, default='{}')  # JSON string of params
    version = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
