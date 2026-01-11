# app/init_db.py
import os
from .db import engine, Base

def init_db():
    """
    Creates tables. Enable on Railway by setting:
    RUN_DB_INIT=true
    """
    if os.getenv("RUN_DB_INIT", "").lower() in ("1", "true", "yes", "on"):
        print("RUN_DB_INIT enabled; running Base.metadata.create_all()...")
        Base.metadata.create_all(bind=engine)
    else:
        print("RUN_DB_INIT not enabled; skipping Base.metadata.create_all().")
