# app/init_db.py
import os
from .db import engine, Base
from . import models_hospitals  # noqa: F401
from . import models_providers  # noqa: F401
from .models_providers import PatientProviderSelection  # noqa: F401



def init_db():
    """
    Creates tables if RUN_DB_INIT=true.
    """
    run = os.getenv("RUN_DB_INIT", "").lower() in ("1", "true", "yes", "on")
    if not run:
        print("RUN_DB_INIT not enabled; skipping Base.metadata.create_all().")
        return

    print("RUN_DB_INIT enabled; running Base.metadata.create_all()...")
    Base.metadata.create_all(bind=engine)
