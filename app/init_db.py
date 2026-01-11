# app/init_db.py
import os
from .db import Base, engine

def init_db():
    run = os.getenv("RUN_DB_INIT", "").lower() in ("1", "true", "yes", "y")
    if not run:
        print("RUN_DB_INIT not enabled; skipping Base.metadata.create_all().")
        return

    print("RUN_DB_INIT enabled; running Base.metadata.create_all()...")
    Base.metadata.create_all(bind=engine)
