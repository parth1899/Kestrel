from sqlalchemy import Column, String, DateTime, Float, Text, JSON, UniqueConstraint
from sqlalchemy.sql import func
import uuid

from .base import Base


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String, nullable=False, index=True)
    agent_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    recommended_action = Column(String, nullable=False)
    priority = Column(Float, nullable=False, default=1)
    rationale = Column(JSON, nullable=True)  # dict of signals and reasons
    status = Column(String, nullable=False, default="pending")  # pending|executed|dismissed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("alert_id", name="uq_decisions_alert_id"),
    )
