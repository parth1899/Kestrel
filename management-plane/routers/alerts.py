from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
import json

from utils.db import get_db
from schemas import AlertOut


router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _parse_dt(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        # Accept ISO 8601 strings
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid datetime: {dt_str}")


@router.get("/", response_model=List[AlertOut])
def list_alerts(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = Query(None, description="Filter by severity (e.g., low|medium|high|critical)"),
    event_type: Optional[str] = Query(None, description="Filter by event type (e.g., process|network|file|system)"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    min_score: Optional[float] = Query(None, description="Minimum score threshold"),
    since: Optional[str] = Query(None, description="Only alerts since this ISO timestamp"),
    until: Optional[str] = Query(None, description="Only alerts until this ISO timestamp"),
    db: Session = Depends(get_db),
):
    since_dt = _parse_dt(since)
    until_dt = _parse_dt(until)

    where_clauses = []
    params: Dict[str, Any] = {"limit": limit, "offset": offset}

    if severity:
        where_clauses.append("severity = :severity")
        params["severity"] = severity
    if event_type:
        where_clauses.append("event_type = :event_type")
        params["event_type"] = event_type
    if agent_id:
        where_clauses.append("agent_id = :agent_id")
        params["agent_id"] = agent_id
    if min_score is not None:
        where_clauses.append("score >= :min_score")
        params["min_score"] = min_score
    if since_dt is not None:
        where_clauses.append("created_at >= :since")
        params["since"] = since_dt
    if until_dt is not None:
        where_clauses.append("created_at <= :until")
        params["until"] = until_dt

    where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    sql = text(
        f"""
        SELECT 
            id::text AS id,
            event_id::text AS event_id,
            agent_id,
            event_type,
            score::float AS score,
            severity,
            source,
            details::text AS details_text,
            created_at
        FROM alerts
        {where_sql}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
        """
    )

    rows = db.execute(sql, params).mappings().all()
    out: List[AlertOut] = []
    for r in rows:
        details: Any
        dtxt = r.get("details_text")
        if isinstance(dtxt, str):
            try:
                details = json.loads(dtxt)
            except Exception:
                # If it's not valid JSON, wrap it in a fallback
                details = {"raw": dtxt}
        elif dtxt is None:
            details = {}
        else:
            # In some drivers JSONB comes back as dict already
            details = dtxt  # type: ignore

        out.append(
            AlertOut(
                id=r["id"],
                event_id=r["event_id"],
                agent_id=r["agent_id"],
                event_type=r["event_type"],
                score=float(r["score"]),
                severity=r["severity"],
                source=r["source"],
                details=details,
                timestamp=r["created_at"].isoformat() if r["created_at"] else "",
            )
        )

    return out


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: str, db: Session = Depends(get_db)):
    sql = text(
        """
        SELECT 
            id::text AS id,
            event_id::text AS event_id,
            agent_id,
            event_type,
            score::float AS score,
            severity,
            source,
            details::text AS details_text,
            created_at
        FROM alerts
        WHERE id::text = :alert_id
        LIMIT 1
        """
    )
    row = db.execute(sql, {"alert_id": alert_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")

    dtxt = row.get("details_text")
    if isinstance(dtxt, str):
        try:
            details = json.loads(dtxt)
        except Exception:
            details = {"raw": dtxt}
    elif dtxt is None:
        details = {}
    else:
        details = dtxt  # type: ignore

    return AlertOut(
        id=row["id"],
        event_id=row["event_id"],
        agent_id=row["agent_id"],
        event_type=row["event_type"],
        score=float(row["score"]),
        severity=row["severity"],
        source=row["source"],
        details=details,
        timestamp=row["created_at"].isoformat() if row["created_at"] else "",
    )
