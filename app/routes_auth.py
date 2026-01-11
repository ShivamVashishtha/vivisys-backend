# app/routes_auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: EmailStr
    password: str
    role: str  # "guardian" | "doctor" | "patient" | "clinic_admin"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse)
def register(payload: AuthRequest):
    # TODO: replace with your real register logic
    # For now, just return a dummy token so the frontend can proceed.
    return TokenResponse(access_token="dev_register_token")


@router.post("/login", response_model=TokenResponse)
def login(payload: AuthRequest):
    # TODO: replace with your real auth logic
    # For now, just return a dummy token so the frontend can proceed.
    return TokenResponse(access_token="dev_login_token")
