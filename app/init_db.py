# app/init_db.py
import os
import logging

from .db import Base, engine
from . import models  # noqa: F401  (ensures models are imported)

logger = logging.getLogger(__name__)

def init_db():
    if os.getenv("RUN_DB_INIT", "").lower() not in ("1", "true", "yes", "on"):
        logger.info("RUN_DB_INIT not enabled; skipping Base.metadata.create_all().")
        return

    Base.metadata.create_all(bind=engine)
    logger.info("DB init complete: Base.metadata.create_all() ran.")
