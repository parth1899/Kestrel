import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import HTTPException, status
from jose import jwt, JWTError
import bcrypt
from sqlalchemy.orm import Session

from utils.db import SessionLocal
from models import User

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
# Prefer a bcrypt hash for the admin password; plain ADMIN_PASSWORD is deprecated
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")
ADMIN_PASSWORD_PLAIN = os.getenv("ADMIN_PASSWORD")


def create_access_token(subject: str, extra: Optional[Dict[str, Any]] = None, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes or JWT_EXPIRE_MINUTES)
    to_encode: Dict[str, Any] = {"sub": subject, "exp": expire}
    if extra:
        to_encode.update(extra)
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def verify_credentials(username: str, password: str) -> bool:
    # Username must match
    if username != ADMIN_USERNAME:
        return False

    # Require bcrypt hash if provided
    if ADMIN_PASSWORD_HASH:
        try:
            stored_hash = ADMIN_PASSWORD_HASH.encode("utf-8")
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash)
        except Exception:
            # If hash is malformed, deny auth
            return False

    # Fallback (deprecated): allow plain env for dev only
    if ADMIN_PASSWORD_PLAIN is not None:
        return password == ADMIN_PASSWORD_PLAIN

    # No configured credentials
    return False


def hash_password(password: str) -> str:
    """Helper to create a bcrypt hash for a given password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username, User.is_active == True).first()  # noqa: E712


def get_current_user(token: str) -> Optional[Dict[str, Any]]:
    payload = decode_token(token)
    return payload
