from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from utils.db import get_db
from models import Rule
from schemas import RuleCreate, RuleUpdate, RuleOut
from .auth import require_auth

router = APIRouter()


@router.get("/", response_model=List[RuleOut])
def list_rules(db: Session = Depends(get_db)):
    return db.query(Rule).all()


@router.post("/", response_model=RuleOut, status_code=201, dependencies=[Depends(require_auth)])
def create_rule(payload: RuleCreate, db: Session = Depends(get_db)):
    obj = Rule(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{rule_id}", response_model=RuleOut)
def get_rule(rule_id: str, db: Session = Depends(get_db)):
    obj = db.query(Rule).get(rule_id)
    if not obj:
        raise HTTPException(404, detail="Rule not found")
    return obj


@router.patch("/{rule_id}", response_model=RuleOut, dependencies=[Depends(require_auth)])
def update_rule(rule_id: str, payload: RuleUpdate, db: Session = Depends(get_db)):
    obj = db.query(Rule).get(rule_id)
    if not obj:
        raise HTTPException(404, detail="Rule not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{rule_id}", status_code=204, dependencies=[Depends(require_auth)])
def delete_rule(rule_id: str, db: Session = Depends(get_db)):
    obj = db.query(Rule).get(rule_id)
    if not obj:
        raise HTTPException(404, detail="Rule not found")
    db.delete(obj)
    db.commit()
    return None
