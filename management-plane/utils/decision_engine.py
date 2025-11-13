import json
import uuid
from typing import Any, Dict, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import SessionLocal

import logging

logger = logging.getLogger("decision_engine")


def _recommend_action(alert: Dict[str, Any]) -> Dict[str, Any]:
    # Simple heuristic based on alert details
    details = alert.get("details", {}) or {}
    features = details.get("features", {}) or {}
    reasons = details.get("reasons", {}) or {}

    severity = alert.get("severity", "low")
    event_type = alert.get("event_type", "unknown")
    score = float(alert.get("score", 0))

    action = "notify_soc"
    priority = 1.0
    rationale = {"features": features, "reasons": reasons}

    # High severity or high score -> isolate host
    if severity in ("critical", "high") or score >= 80:
        action = "isolate_host"
        priority = 5.0
    # Process indicators
    elif event_type == "process":
        if features.get("hash_known_malicious") or (features.get("vt_positives", 0) or 0) > 50:
            action = "terminate_process"
            priority = 4.0
        elif features.get("is_suspicious_path"):
            action = "quarantine_file"
            priority = 3.0
    # Network indicators
    elif event_type == "network":
        if not features.get("is_private_ip") and not features.get("is_loopback"):
            action = "block_ip"
            priority = 3.5
    # File indicators
    elif event_type == "file":
        if (features.get("yara_hits_count", 0) or 0) > 0:
            action = "quarantine_file"
            priority = 3.5

    # Anomaly/behavioral reasons boost
    if reasons.get("anomaly"):
        priority = max(priority, 2.5)
    if reasons.get("behavioral"):
        priority = max(priority, 2.0)

    return {"recommended_action": action, "priority": priority, "rationale": rationale}


def run_once(db: Optional[Session] = None) -> int:
    """One pass: read recent alerts without associated decisions and create decisions."""
    close = False
    if db is None:
        db = SessionLocal()
        close = True
    try:
        # Find alerts in last 24h not in decisions. Cast alerts.id::text to match decisions.alert_id (varchar).
        sql = text(
            """
            SELECT a.id::text AS id, a.event_id::text AS event_id, a.agent_id, a.event_type, a.score::float AS score,
                   a.severity, a.source, a.details::text AS details_text, a.created_at
            FROM alerts a
            LEFT JOIN decisions d ON d.alert_id = a.id::text
            WHERE d.alert_id IS NULL
              AND a.created_at >= NOW() - INTERVAL '24 hours'
            ORDER BY a.created_at DESC
            LIMIT 200
            """
        )
        rows = db.execute(sql).mappings().all()
        created = 0
        for r in rows:
            dtxt = r.get("details_text")
            try:
                details = json.loads(dtxt) if isinstance(dtxt, str) else (dtxt or {})
            except Exception:
                details = {"raw": dtxt}
            alert = {
                "id": r["id"],
                "event_id": r["event_id"],
                "agent_id": r["agent_id"],
                "event_type": r["event_type"],
                "score": float(r["score"]),
                "severity": r["severity"],
                "source": r["source"],
                "details": details,
                "timestamp": r["created_at"].isoformat() if r["created_at"] else "",
            }
            rec = _recommend_action(alert)
            ins = text(
                """
                INSERT INTO decisions (
                    id, alert_id, agent_id, event_type, severity, score,
                    recommended_action, priority, rationale, status, created_at
                ) VALUES (
                    :id, :alert_id, :agent_id, :event_type, :severity, :score,
                    :recommended_action, :priority, :rationale, 'pending', NOW()
                )
                ON CONFLICT (alert_id) DO NOTHING
                """
            )
            params = {
                "id": str(uuid.uuid4()),
                "alert_id": alert["id"],
                "agent_id": alert["agent_id"],
                "event_type": alert["event_type"],
                "severity": alert["severity"],
                "score": alert["score"],
                "recommended_action": rec["recommended_action"],
                "priority": rec["priority"],
                "rationale": json.dumps(rec["rationale"]),  # JSON column adapts automatically
            }
            db.execute(ins, params)
            created += 1
        if created:
            db.commit()
        if created:
            logger.info(f"Decision engine created {created} decisions")
        return created
    finally:
        if close:
            db.close()
