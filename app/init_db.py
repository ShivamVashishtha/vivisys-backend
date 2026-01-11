# app/init_db.py
from .db import engine, Base

def init_db() -> None:
    Base.metadata.create_all(bind=engine)
