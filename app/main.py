# app/main.py
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.init_db import init_db

app = FastAPI()

# CORS (adjust origins later if needed)
origins_env = os.getenv("CORS_ORIGINS", "*")
origins = ["*"] if origins_env.strip() == "*" else [o.strip() for o in origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}
