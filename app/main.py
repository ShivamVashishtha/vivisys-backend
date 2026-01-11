# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .init_db import init_db

# import your routers
from .routes_auth import router as auth_router
from .routes_patients import router as patients_router
from .routes_consents import router as consents_router
from .routes_records import router as records_router

app = FastAPI(title="ViviSys API")

# IMPORTANT: CORS must be added BEFORE requests hit routes
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://vivisys.net",
    "https://www.vivisys.net",
]

# If you want quick dev-mode CORS, you can set:
# CORS_ALLOW_ALL=true
if os.getenv("CORS_ALLOW_ALL", "").lower() in ("1", "true", "yes", "on"):
    allow_origins = ["*"]
else:
    allow_origins = ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,  # keep False when using "*" origins
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}

# Routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(patients_router, tags=["patients"])
app.include_router(consents_router, prefix="/consents", tags=["consents"])
app.include_router(records_router, prefix="/records", tags=["records"])
