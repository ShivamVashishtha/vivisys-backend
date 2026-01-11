# app/db.py
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


def _normalize_db_url(url: str) -> str:
    """
    Railway sometimes gives:
      - postgres://...
      - postgresql://...
    SQLAlchemy wants postgresql+psycopg2://...
    """
    url = url.strip()

    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    if url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

    return url


DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    # Local fallback (change if you want)
    DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
else:
    DATABASE_URL = _normalize_db_url(DATABASE_URL)

# If you used Railway public proxy URL, SSL is usually required.
# psycopg2 supports sslmode in querystring:
# postgresql+psycopg2://.../railway?sslmode=require
# If you didn't include it, we can optionally append it:
if "rlwy.net" in DATABASE_URL and "sslmode=" not in DATABASE_URL:
    sep = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{sep}sslmode=require"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
