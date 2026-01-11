# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .init_db import init_db

# IMPORTANT: make sure these exist in your repo
from .routes_auth import router as auth_router
from .routes_patients import router as patients_router
from .routes_records import router as records_router
from .routes_consents import router as consents_router


def _split_origins(value: str) -> list[str]:
    # supports comma-separated
    return [v.strip() for v in value.split(",") if v.strip()]


app = FastAPI()

# ---- CORS (fixes OPTIONS 400 + browser "Failed to fetch") ----
cors_env = os.getenv("CORS_ORIGINS", "").strip()
if cors_env:
    allow_origins = _split_origins(cors_env)
else:
    # default safe list
    allow_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://vivisys.net",
        # add your Netlify preview domain(s) if needed
        # "https://<your-site>.netlify.app",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://vivisys.net",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Routers ----
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(consents_router)
app.include_router(records_router)

@app.get("/health")
def health():
    return {"status": "ok"}

# ---- Optional: create tables on startup (only if RUN_DB_INIT=1) ----
RUN_DB_INIT = os.getenv("RUN_DB_INIT", "0").lower() in ("1", "true", "yes", "on")

@app.on_event("startup")
def _startup():
    if RUN_DB_INIT:
        print("RUN_DB_INIT enabled; running Base.metadata.create_all()...")
        init_db()
    else:
        print("RUN_DB_INIT not enabled; skipping Base.metadata.create_all().")
