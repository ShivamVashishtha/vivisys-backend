from .db import engine, Base
from . import models  # noqa: F401

import os
from app.db import engine
from app.models import Base  # <-- adjust if your Base is located elsewhere

def init_db() -> None:
    # Optional: gate init behind flag so you can control it in prod
    run_init = os.getenv("RUN_DB_INIT", "false").lower() in {"1", "true", "yes"}

    if engine is None:
        print("DATABASE_URL not set; skipping DB init.")
        return

    if not run_init:
        print("RUN_DB_INIT not enabled; skipping Base.metadata.create_all().")
        return

    Base.metadata.create_all(bind=engine)
    print("DB init done: Base.metadata.create_all()")

