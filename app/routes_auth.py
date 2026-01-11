# app/routes_auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .db import get_db
from . import crud
from .schemas import RegisterIn, LoginIn, TokenOut
from .security import verify_password, hash_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = crud.create_user(
        db,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
    )

    token = create_access_token({"sub": user.email, "role": user.role, "user_id": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # (optional) ensure role matches what frontend selected
    if data.role and user.role != data.role:
        raise HTTPException(status_code=401, detail="Role mismatch")

    token = create_access_token({"sub": user.email, "role": user.role, "user_id": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
