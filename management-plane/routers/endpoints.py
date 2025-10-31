from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from utils.db import get_db
from models import Endpoint
from schemas import EndpointCreate, EndpointUpdate, EndpointOut
from .auth import require_auth

router = APIRouter()


@router.get("/", response_model=List[EndpointOut])
def list_endpoints(db: Session = Depends(get_db)):
    return db.query(Endpoint).all()


@router.post("/", response_model=EndpointOut, status_code=201, dependencies=[Depends(require_auth)])
def create_endpoint(payload: EndpointCreate, db: Session = Depends(get_db)):
    obj = Endpoint(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{endpoint_id}", response_model=EndpointOut)
def get_endpoint(endpoint_id: str, db: Session = Depends(get_db)):
    obj = db.query(Endpoint).get(endpoint_id)
    if not obj:
        raise HTTPException(404, detail="Endpoint not found")
    return obj


@router.patch("/{endpoint_id}", response_model=EndpointOut, dependencies=[Depends(require_auth)])
def update_endpoint(endpoint_id: str, payload: EndpointUpdate, db: Session = Depends(get_db)):
    obj = db.query(Endpoint).get(endpoint_id)
    if not obj:
        raise HTTPException(404, detail="Endpoint not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{endpoint_id}", status_code=204, dependencies=[Depends(require_auth)])
def delete_endpoint(endpoint_id: str, db: Session = Depends(get_db)):
    obj = db.query(Endpoint).get(endpoint_id)
    if not obj:
        raise HTTPException(404, detail="Endpoint not found")
    db.delete(obj)
    db.commit()
    return None
