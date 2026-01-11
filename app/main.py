import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .init_db import init_db

# IMPORTANT: import routers that define your endpoints
from .routes_auth import router as auth_router
from .routes_patients import router as patients_router
from .routes_consents import router as consents_router
from .routes_records import router as records_router

app = FastAPI(title="ViviSys API")

# ---- CORS ----
# Put this env var on Railway:
# CORS_ORIGINS="https://vivisys.net,https://www.vivisys.net,http://localhost:3000"
origins_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,https://vivisys.net,https://www.vivisys.net",
)
origins = [o.strip() for o in origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # <-- this is what prevents OPTIONS 400
    allow_headers=["*"],   # <-- this is what prevents OPTIONS 400
)

# ---- Routers ----
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(consents_router)
app.include_router(records_router)

@app.get("/health")
def health():
    return {"ok": True}

@app.on_event("startup")
def _startup():
    # If RUN_DB_INIT=1, create tables on startup
    init_db()
