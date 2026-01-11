# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .init_db import init_db
from .routes_auth import router as auth_router
from .routes_patients import router as patients_router
from .routes_consents import router as consents_router
from .routes_records import router as records_router

app = FastAPI(title="Medaryx API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # add your Netlify domain here too, e.g.
        # "https://YOUR-SITE.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

# IMPORTANT: mount each router WITHOUT adding another prefix here
# (the router files will own their prefixes)
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(consents_router)
app.include_router(records_router)

# Optional: print routes at boot so you can confirm /auth/login exists
for r in app.routes:
    methods = getattr(r, "methods", None)
    path = getattr(r, "path", None)
    if methods and path:
        print(sorted(list(methods)), path)
