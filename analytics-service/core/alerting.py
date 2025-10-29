import uuid
import json
from core.models import Alert
from utils.db import SessionLocal, engine
from utils.logger import log
from sqlalchemy import text
from datetime import datetime
import aio_pika


async def publish_alert(exchange, alert: Alert, config: dict):
    try:
        # Serialize alert
        body = json.dumps({
            "id": str(alert.id),
            "event_id": str(alert.event_id),
            "agent_id": alert.agent_id,
            "event_type": alert.event_type,
            "score": alert.score,
            "severity": alert.severity,
            "source": alert.source,
            "details": alert.details,
            "timestamp": datetime.now().isoformat()
        }).encode()

        message = aio_pika.Message(
            body=body,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )

        routing_key = f"alerts.{alert.severity}"
        await exchange.publish(message, routing_key=routing_key)
        log.info(f"Alert published to {routing_key}")

    except Exception as e:
        log.error(f"Failed to publish alert: {e}")

def write_alert_to_db(alert: Alert):
    with engine.connect() as conn:
        try:
            # ← Serialize dict to JSON string
            details_json = json.dumps(alert.details)
            
            conn.execute(
                text("""
                    INSERT INTO alerts (
                        id, event_id, agent_id, event_type, score, 
                        severity, source, details, created_at
                    ) VALUES (
                        :id, :event_id, :agent_id, :event_type, :score,
                        :severity, :source, :details, NOW()
                    )
                """),
                {
                    "id": alert.id,
                    "event_id": alert.event_id,
                    "agent_id": alert.agent_id,
                    "event_type": alert.event_type,
                    "score": alert.score,
                    "severity": alert.severity,
                    "source": alert.source,
                    "details": details_json  # ← JSON string
                }
            )
            conn.commit()
            log.info("Alert written to DB")
        except Exception as e:
            log.error(f"Failed to write alert to DB: {e}")
            conn.rollback()