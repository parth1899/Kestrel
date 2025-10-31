from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from utils.db import get_db
from models import DetectorConfig
from schemas import DetectorConfigCreate, DetectorConfigUpdate, DetectorConfigOut
from .auth import require_auth

router = APIRouter()


@router.get("/", response_model=List[DetectorConfigOut])
def list_detector_configs(db: Session = Depends(get_db)):
    return db.query(DetectorConfig).all()


@router.post("/", response_model=DetectorConfigOut, status_code=201, dependencies=[Depends(require_auth)])
def create_detector_config(payload: DetectorConfigCreate, db: Session = Depends(get_db)):
    obj = DetectorConfig(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{config_id}", response_model=DetectorConfigOut)
def get_detector_config(config_id: str, db: Session = Depends(get_db)):
    obj = db.query(DetectorConfig).get(config_id)
    if not obj:
        raise HTTPException(404, detail="Detector config not found")
    return obj


@router.patch("/{config_id}", response_model=DetectorConfigOut, dependencies=[Depends(require_auth)])
def update_detector_config(config_id: str, payload: DetectorConfigUpdate, db: Session = Depends(get_db)):
    obj = db.query(DetectorConfig).get(config_id)
    if not obj:
        raise HTTPException(404, detail="Detector config not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{config_id}", status_code=204, dependencies=[Depends(require_auth)])
def delete_detector_config(config_id: str, db: Session = Depends(get_db)):
    obj = db.query(DetectorConfig).get(config_id)
    if not obj:
        raise HTTPException(404, detail="Detector config not found")
    db.delete(obj)
    db.commit()
    return None
