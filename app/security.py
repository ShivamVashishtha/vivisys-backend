import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "60"))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str, extra: Dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=JWT_EXPIRES_MIN)

    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if extra:
        payload.update(extra)

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
