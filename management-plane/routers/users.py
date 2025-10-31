from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from utils.db import get_db
from models import User
from schemas import UserCreate, UserUpdate, UserOut
from .auth import require_role
from utils.security import hash_password

router = APIRouter()


@router.get("/", response_model=List[UserOut], dependencies=[Depends(require_role("admin"))])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.post("/", response_model=UserOut, status_code=201, dependencies=[Depends(require_role("admin"))])
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(409, detail="Username already exists")
    u = User(username=payload.username, password_hash=hash_password(payload.password), role=payload.role)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.get("/{user_id}", response_model=UserOut, dependencies=[Depends(require_role("admin"))])
def get_user(user_id: str, db: Session = Depends(get_db)):
    u = db.query(User).get(user_id)
    if not u:
        raise HTTPException(404, detail="User not found")
    return u


@router.patch("/{user_id}", response_model=UserOut, dependencies=[Depends(require_role("admin"))])
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db)):
    u = db.query(User).get(user_id)
    if not u:
        raise HTTPException(404, detail="User not found")
    data = payload.dict(exclude_unset=True)
    if "password" in data:
        u.password_hash = hash_password(data.pop("password"))
    for k, v in data.items():
        setattr(u, k, v)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.delete("/{user_id}", status_code=204, dependencies=[Depends(require_role("admin"))])
def delete_user(user_id: str, db: Session = Depends(get_db)):
    u = db.query(User).get(user_id)
    if not u:
        raise HTTPException(404, detail="User not found")
    db.delete(u)
    db.commit()
    return None
