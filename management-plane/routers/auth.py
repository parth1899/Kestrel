from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from sqlalchemy.orm import Session

from utils.db import get_db
from utils.security import (
    create_access_token,
    decode_token,
    verify_credentials,
    get_user_by_username,
    verify_password,
)
from models import User

router = APIRouter()
security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # First try DB-backed users
    user = get_user_by_username(db, payload.username)
    if user and verify_password(payload.password, user.password_hash):
        token = create_access_token(subject=user.username, extra={"uid": user.id, "role": user.role})
        return {"access_token": token, "token_type": "bearer"}

    # Fallback to env-configured admin (for bootstrapping)
    if verify_credentials(payload.username, payload.password):
        token = create_access_token(subject=payload.username, extra={"role": "admin"})
        return {"access_token": token, "token_type": "bearer"}

    raise HTTPException(status_code=401, detail="Invalid username or password")


# A reusable dependency to enforce auth on protected routes

def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is None or not credentials.scheme.lower() == "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")
    decode_token(credentials.credentials)
    return True


def require_role(required: str):
    def _inner(credentials: HTTPAuthorizationCredentials = Depends(security)):
        if credentials is None or not credentials.scheme.lower() == "bearer":
            raise HTTPException(status_code=401, detail="Missing bearer token")
        payload = decode_token(credentials.credentials)
        role = payload.get("role")
        if role != required:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return True

    return _inner
