from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.entities import User, UserRole, IdentityStatus, ProfessionalStatus
from backend.app.schemas.dtos import UserRegisterRequest, UserLoginRequest, TokenResponse, UserPublicProfile
from backend.app.security.auth_guard import (
    hash_password, verify_password, create_access_token, get_current_user
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    # Check if email is already taken
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="البريد الإلكتروني مسجل بالفعل، يرجى تسجيل الدخول"
        )

    # Initial trust states (Strict separation of privileges)
    new_user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        role=payload.role,
        identity_status=IdentityStatus.PENDING,
        professional_status=ProfessionalStatus.NOT_APPLIED if payload.role == UserRole.BUYER else ProfessionalStatus.PENDING
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.id, "role": new_user.role.value})
    return TokenResponse(
        access_token=token,
        user_id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        identity_status=new_user.identity_status,
        professional_status=new_user.professional_status
    )

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="بيانات الاعتماد غير صحيحة، يرجى التأكد من البريد أو كلمة المرور"
        )
    if user.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="تم تعليق هذا الحساب لمخالفته شروط الخدمة"
        )

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        identity_status=user.identity_status,
        professional_status=user.professional_status
    )

@router.get("/me", response_model=TokenResponse)
def get_me(current_user: User = Depends(get_current_user)):
    token = create_access_token({"sub": current_user.id, "role": current_user.role.value})
    return TokenResponse(
        access_token=token,
        user_id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        identity_status=current_user.identity_status,
        professional_status=current_user.professional_status
    )
