# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .init_db import init_db

# Import your routers
from .routes_auth import router as auth_router
from .routes_patients import router as patients_router
from .routes_records import router as records_router
from .routes_consents import router as consents_router


def _parse_origins() -> list[str]:
    """
    CORS_ORIGINS can be:
      - "*" (not recommended if you ever use cookies/credentials)
      - comma-separated list
    """
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        # safe defaults for your setup
        return [
            "https://vivisys.net",
            "https://www.vivisys.net",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    if raw == "*":
        return ["*"]
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]


app = FastAPI(title="ViviSys Backend")

origins = _parse_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,  # keep False since you're using Bearer tokens, not cookies
    allow_methods=["*"],      # THIS fixes preflight OPTIONS 400
    allow_headers=["*"],      # allow Authorization header
)


@app.on_event("startup")
def _startup():
    # create tables (only when RUN_DB_INIT=true)
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


# Mount routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(patients_router, tags=["patients"])
app.include_router(records_router, prefix="/records", tags=["records"])
app.include_router(consents_router, prefix="/consents", tags=["consents"])
