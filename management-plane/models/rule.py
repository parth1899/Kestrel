from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.sql import func
import uuid

from .base import Base


class Rule(Base):
    __tablename__ = "rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # rule_based | behavioral | anomaly
    definition = Column(Text, nullable=False)  # JSON or DSL string
    enabled = Column(Boolean, nullable=False, default=True)
    policy_id = Column(String, ForeignKey("policies.id", ondelete="CASCADE"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
