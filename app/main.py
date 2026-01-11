# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .init_db import init_db
from .routes_auth import router as auth_router
from .routes_patients import router as patients_router
from .routes_consents import router as consents_router
from .routes_records import router as records_router

app = FastAPI(title="ViviSys API")

# ✅ CORS: allow your frontend domains
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",

    "https://vivisys.net",
    "https://www.vivisys.net",

    # (optional) if you also use a Netlify preview/staging domain, add it here
    # "https://<your-site>.netlify.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    if os.getenv("RUN_DB_INIT", "0") == "1":
        print("RUN_DB_INIT enabled; running Base.metadata.create_all()...")
        init_db()
    else:
        print("RUN_DB_INIT not enabled; skipping Base.metadata.create_all().")

@app.get("/health")
def health():
    return {"ok": True}

# Routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(patients_router, tags=["patients"])
app.include_router(consents_router, prefix="/consents", tags=["consents"])
app.include_router(records_router, prefix="/records", tags=["records"])
