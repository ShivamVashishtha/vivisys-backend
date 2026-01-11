# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .init_db import init_db

# Routers
from .routes_auth import router as auth_router
from .routes_patients import router as patients_router
from .routes_consents import router as consents_router
from .routes_records import router as records_router

# ✅ NEW: mock FHIR router
from .routes_fhir import router as fhir_router

app = FastAPI(title="ViviSys API")

# ---- CORS ----
origins_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,https://vivisys.net,https://www.vivisys.net",
)
origins = [o.strip() for o in origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Routers ----
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(consents_router)
app.include_router(records_router)

# ✅ NEW: serve /fhir inside this same API
# (this makes http://localhost:8080/fhir/... valid in Railway)
app.include_router(fhir_router)

@app.get("/health")
def health():
    return {"ok": True}

@app.on_event("startup")
def _startup():
    init_db()
