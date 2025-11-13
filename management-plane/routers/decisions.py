from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
import json

from utils.db import get_db
from schemas import DecisionOut
from utils.decision_engine import run_once


router = APIRouter(prefix="/api/decisions", tags=["decisions"]) 


@router.get("/", response_model=List[DecisionOut])
def list_decisions(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    where = " WHERE status = :status" if status else ""
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    sql = text(
        f"""
        SELECT 
            id::text AS id,
            alert_id::text AS alert_id,
            agent_id,
            event_type,
            severity,
            score::float AS score,
            recommended_action,
            priority::float AS priority,
            rationale::text AS rationale_text,
            status,
            created_at,
            updated_at
        FROM decisions
        {where}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
        """
    )
    rows = db.execute(sql, params).mappings().all()
    out: List[DecisionOut] = []
    for r in rows:
        rt = r.get("rationale_text")
        if isinstance(rt, str):
            try:
                rationale = json.loads(rt)
            except Exception:
                rationale = {"raw": rt}
        else:
            rationale = rt
        out.append(
            DecisionOut(
                id=r["id"],
                alert_id=r["alert_id"],
                agent_id=r["agent_id"],
                event_type=r["event_type"],
                severity=r["severity"],
                score=float(r["score"]),
                recommended_action=r["recommended_action"],
                priority=float(r["priority"]),
                rationale=rationale,
                status=r["status"],
                created_at=r["created_at"].isoformat() if r["created_at"] else None,
                updated_at=r["updated_at"].isoformat() if r["updated_at"] else None,
            )
        )
    return out


@router.post("/run")
def run_decision_engine(db: Session = Depends(get_db)):
    """Manually trigger one pass of the decision engine and return count created."""
    created = run_once(db)
    return {"created": created}


@router.post("/{decision_id}/execute", response_model=DecisionOut)
def execute_decision(decision_id: str, db: Session = Depends(get_db)):
    # Mark as executed
    update_sql = text("UPDATE decisions SET status='executed', updated_at=NOW() WHERE id::text = :id")
    db.execute(update_sql, {"id": decision_id})
    db.commit()
    # Return updated row
    return get_decision(decision_id, db)


@router.post("/{decision_id}/dismiss", response_model=DecisionOut)
def dismiss_decision(decision_id: str, db: Session = Depends(get_db)):
    update_sql = text("UPDATE decisions SET status='dismissed', updated_at=NOW() WHERE id::text = :id")
    db.execute(update_sql, {"id": decision_id})
    db.commit()
    return get_decision(decision_id, db)


@router.get("/{decision_id}", response_model=DecisionOut)
def get_decision(decision_id: str, db: Session = Depends(get_db)):
    sql = text(
        """
        SELECT 
            id::text AS id,
            alert_id::text AS alert_id,
            agent_id,
            event_type,
            severity,
            score::float AS score,
            recommended_action,
            priority::float AS priority,
            rationale::text AS rationale_text,
            status,
            created_at,
            updated_at
        FROM decisions
        WHERE id::text = :id
        LIMIT 1
        """
    )
    row = db.execute(sql, {"id": decision_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Decision not found")
    rt = row.get("rationale_text")
    if isinstance(rt, str):
        try:
            rationale = json.loads(rt)
        except Exception:
            rationale = {"raw": rt}
    else:
        rationale = rt
    return DecisionOut(
        id=row["id"],
        alert_id=row["alert_id"],
        agent_id=row["agent_id"],
        event_type=row["event_type"],
        severity=row["severity"],
        score=float(row["score"]),
        recommended_action=row["recommended_action"],
        priority=float(row["priority"]),
        rationale=rationale,
        status=row["status"],
        created_at=row["created_at"].isoformat() if row["created_at"] else None,
        updated_at=row["updated_at"].isoformat() if row["updated_at"] else None,
    )
