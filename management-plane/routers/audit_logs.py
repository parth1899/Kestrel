from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from utils.db import get_db
from models import AuditLog
from schemas import AuditLogCreate, AuditLogOut
from .auth import require_auth

router = APIRouter()


@router.get("/", response_model=List[AuditLogOut])
def list_audit_logs(db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(500).all()


@router.post("/", response_model=AuditLogOut, status_code=201, dependencies=[Depends(require_auth)])
def create_audit_log(payload: AuditLogCreate, db: Session = Depends(get_db)):
    obj = AuditLog(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
