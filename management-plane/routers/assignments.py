from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from utils.db import get_db
from models import Assignment
from schemas import AssignmentCreate, AssignmentUpdate, AssignmentOut
from .auth import require_auth

router = APIRouter()


@router.get("/", response_model=List[AssignmentOut])
def list_assignments(db: Session = Depends(get_db)):
    return db.query(Assignment).all()


@router.post("/", response_model=AssignmentOut, status_code=201, dependencies=[Depends(require_auth)])
def create_assignment(payload: AssignmentCreate, db: Session = Depends(get_db)):
    obj = Assignment(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{assignment_id}", response_model=AssignmentOut)
def get_assignment(assignment_id: str, db: Session = Depends(get_db)):
    obj = db.query(Assignment).get(assignment_id)
    if not obj:
        raise HTTPException(404, detail="Assignment not found")
    return obj


@router.patch("/{assignment_id}", response_model=AssignmentOut, dependencies=[Depends(require_auth)])
def update_assignment(assignment_id: str, payload: AssignmentUpdate, db: Session = Depends(get_db)):
    obj = db.query(Assignment).get(assignment_id)
    if not obj:
        raise HTTPException(404, detail="Assignment not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{assignment_id}", status_code=204, dependencies=[Depends(require_auth)])
def delete_assignment(assignment_id: str, db: Session = Depends(get_db)):
    obj = db.query(Assignment).get(assignment_id)
    if not obj:
        raise HTTPException(404, detail="Assignment not found")
    db.delete(obj)
    db.commit()
    return None
