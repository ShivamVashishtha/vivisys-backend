from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .db import get_db
from .schemas import RegisterIn, TokenOut
from . import crud
from .auth import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db, data.email, data.password, data.role)
    token = create_access_token(user.id, user.role)
    return TokenOut(access_token=token)

@router.post("/login", response_model=TokenOut)
def login(data: RegisterIn, db: Session = Depends(get_db)):
    user = crud.authenticate(db, data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id, user.role)
    return TokenOut(access_token=token)
