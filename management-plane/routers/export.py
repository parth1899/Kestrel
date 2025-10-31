from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from utils.db import get_db
from models import Rule, DetectorConfig

router = APIRouter()


@router.get("/rules")
def export_rules(db: Session = Depends(get_db)) -> Dict[str, Any]:
    rules = db.query(Rule).filter(Rule.enabled == True).all()  # noqa: E712
    # Return a simple consumable structure
    return {
        "rules": [
            {
                "id": r.id,
                "name": r.name,
                "type": r.type,
                "definition": r.definition,
                "policy_id": r.policy_id,
            }
            for r in rules
        ]
    }


@router.get("/detectors")
def export_detector_configs(db: Session = Depends(get_db)) -> Dict[str, Any]:
    configs = db.query(DetectorConfig).all()
    return {
        "detectors": [
            {
                "id": c.id,
                "detector_name": c.detector_name,
                "params": c.params,
                "version": c.version,
            }
            for c in configs
        ]
    }
