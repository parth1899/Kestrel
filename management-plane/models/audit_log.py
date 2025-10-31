from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
import uuid

from .base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    actor = Column(String, nullable=True)  # user id or system
    action = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
