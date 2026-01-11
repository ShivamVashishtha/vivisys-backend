# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .init_db import init_db

from .routes_auth import router as auth_router
from .routes_patients import router as patients_router
from .routes_consents import router as consents_router
from .routes_records import router as records_router

app = FastAPI()

# ✅ CORS (must be added immediately after app = FastAPI())
# Put your real frontend URL(s) in Railway env var CORS_ORIGINS as comma-separated.
# Example:
# CORS_ORIGINS=https://your-site.netlify.app,http://localhost:3000
cors_origins_env = os.getenv("CORS_ORIGINS", "")
origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

# sensible defaults for local dev
if not origins:
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    # Only run create_all if explicitly enabled
    if os.getenv("RUN_DB_INIT", "").lower() in ("1", "true", "yes", "on"):
        print("RUN_DB_INIT enabled; running Base.metadata.create_all()...")
        init_db()
    else:
        print("RUN_DB_INIT not enabled; skipping Base.metadata.create_all().")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(consents_router)
app.include_router(records_router)
