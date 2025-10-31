from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from utils.db import get_db
from models import Policy
from schemas import PolicyCreate, PolicyUpdate, PolicyOut
from .auth import require_auth

router = APIRouter()


@router.get("/", response_model=List[PolicyOut])
def list_policies(db: Session = Depends(get_db)):
    return db.query(Policy).all()


@router.post("/", response_model=PolicyOut, status_code=201, dependencies=[Depends(require_auth)])
def create_policy(payload: PolicyCreate, db: Session = Depends(get_db)):
    obj = Policy(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{policy_id}", response_model=PolicyOut)
def get_policy(policy_id: str, db: Session = Depends(get_db)):
    obj = db.query(Policy).get(policy_id)
    if not obj:
        raise HTTPException(404, detail="Policy not found")
    return obj


@router.patch("/{policy_id}", response_model=PolicyOut, dependencies=[Depends(require_auth)])
def update_policy(policy_id: str, payload: PolicyUpdate, db: Session = Depends(get_db)):
    obj = db.query(Policy).get(policy_id)
    if not obj:
        raise HTTPException(404, detail="Policy not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{policy_id}", status_code=204, dependencies=[Depends(require_auth)])
def delete_policy(policy_id: str, db: Session = Depends(get_db)):
    obj = db.query(Policy).get(policy_id)
    if not obj:
        raise HTTPException(404, detail="Policy not found")
    db.delete(obj)
    db.commit()
    return None
