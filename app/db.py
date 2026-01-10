from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL or ":PORT" in DATABASE_URL or "PORT" in DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing or invalid. On Railway, set DATABASE_URL to the full Postgres connection string "
        "(postgresql://user:pass@host:5432/dbname)."
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
