# app/main.py
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .init_db import init_db

# Import routers (make sure these files exist)
from .routes_auth import router as auth_router
from .routes_patients import router as patients_router
from .routes_consents import router as consents_router
from .routes_records import router as records_router


def _truthy(val: str | None) -> bool:
    return (val or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _build_cors_origins() -> list[str]:
    """
    Railway/production friendly CORS:
    - Set CORS_ORIGINS as comma-separated list in Railway variables
      Example:
        CORS_ORIGINS=https://vivisys.net,https://www.vivisys.net,http://localhost:3000
    - We also include sane defaults.
    """
    raw = (os.getenv("CORS_ORIGINS") or "").strip()
    origins = []

    if raw:
        for part in raw.split(","):
            o = part.strip()
            if o:
                origins.append(o)

    # Defaults (safe + what you’re using)
    defaults = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://vivisys.net",
        "https://www.vivisys.net",
    ]
    for d in defaults:
        if d not in origins:
            origins.append(d)

    return origins


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if _truthy(os.getenv("RUN_DB_INIT")):
        print("RUN_DB_INIT enabled; running Base.metadata.create_all()...")
        init_db()
    else:
        print("RUN_DB_INIT not enabled; skipping Base.metadata.create_all().")

    # (Optional) print routes for debugging
    try:
        for r in app.router.routes:
            methods = getattr(r, "methods", None)
            path = getattr(r, "path", None)
            if methods and path:
                print(sorted(list(methods)), path)
    except Exception:
        pass

    yield
    # Shutdown (nothing needed)


app = FastAPI(
    title="ViviSys Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# --- CORS (MUST be added before requests hit routes) ---
cors_origins = _build_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],   # important for OPTIONS preflight
    allow_headers=["*"],   # important for Authorization header
)

# --- Routes ---
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(consents_router)
app.include_router(records_router)

# --- Health ---
@app.get("/health")
def health():
    return {"ok": True}
