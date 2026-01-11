# app/security.py
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# JWT settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-change-me")  # set in Railway
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))


def create_access_token(
    subject: str,
    role: str,
    expires_minutes: Optional[int] = None,
    extra: Optional[dict[str, Any]] = None,
) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes or JWT_EXPIRES_MINUTES)

    payload: dict[str, Any] = {
        "sub": subject,   # typically email or user_id
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }

    if extra:
        payload.update(extra)

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        raise ValueError("Invalid token") from e
