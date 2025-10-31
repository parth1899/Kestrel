from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
import uuid

from .base import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint_id = Column(String, ForeignKey("endpoints.id", ondelete="CASCADE"), index=True)
    policy_id = Column(String, ForeignKey("policies.id", ondelete="CASCADE"), index=True)
    status = Column(String, nullable=False, default="applied")  # applied | pending | failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
