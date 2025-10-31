from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from .base import Base

try:
    from sqlalchemy import UniqueConstraint
except Exception:
    UniqueConstraint = None


class Endpoint(Base):
    __tablename__ = "endpoints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hostname = Column(String, nullable=False, index=True)
    ip = Column(String, nullable=True)
    os = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")
    tags = Column(String, nullable=True)  # comma-separated simple tag list
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
