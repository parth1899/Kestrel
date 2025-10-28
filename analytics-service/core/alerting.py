import uuid
import json
from core.models import Alert
from utils.db import SessionLocal
from sqlalchemy import text

async def publish_alert(channel, alert: Alert, config):
    if config["service"].get("shadow_mode", False):
        print(f"[SHADOW] Would publish alert: {alert.id}")
        return

    body = alert.model_dump_json().encode()
    channel.basic_publish(
        exchange=config["rabbitmq"]["exchange"],
        routing_key=f"alerts.{alert.severity}",
        body=body
    )

def write_alert_to_db(alert: Alert):
    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO alerts (id, event_id, agent_id, event_type, score, severity, source, details)
            VALUES (:id, :event_id, :agent_id, :event_type, :score, :severity, :source, :details)
        """), alert.dict())
        db.commit()
    finally:
        db.close()