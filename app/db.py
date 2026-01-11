# app/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def _database_url() -> str:
    """
    Priority:
      1) DATABASE_URL (Railway)
      2) DB_URL (optional custom)
      3) local sqlite fallback (for local dev)
    """
    url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
    if not url:
        return "sqlite:///./dev.db"

    # Railway/Heroku sometimes provide postgres:// which SQLAlchemy expects as postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return url


DATABASE_URL = _database_url()

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    FastAPI dependency:
      db = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
