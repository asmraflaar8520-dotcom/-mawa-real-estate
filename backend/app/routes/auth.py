from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.entities import User
from backend.app.schemas.dtos import UserRegisterRequest, UserLoginRequest, TokenResponse
from backend.app.security.auth_guard import (
    get_current_user, get_token_from_header_or_cookie, rate_limit
)
from backend.app.services.auth_service import AuthService

router = APIRouter(tags=["Authentication"])

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))]
)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    return AuthService.register_user(db, payload)

@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))]
)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    return AuthService.login_user(db, payload)

@router.get("/me", response_model=TokenResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return AuthService.get_current_user_profile(current_user)

@router.post("/logout")
def logout(
    token: Optional[str] = Depends(get_token_from_header_or_cookie),
    current_user: User = Depends(get_current_user)
):
    if token:
        AuthService.logout_user(token)
    return {"message": "تم تسجيل الخروج وإبطال الجلسة بنجاح"}
