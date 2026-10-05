from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.models.entities import User, UserRole, IdentityStatus, ProfessionalStatus
from backend.app.schemas.dtos import UserRegisterRequest, UserLoginRequest, TokenResponse
from backend.app.security.auth_guard import (
    hash_password, verify_password, create_access_token, revoke_token
)

class AuthService:
    @staticmethod
    def register_user(db: Session, payload: UserRegisterRequest) -> TokenResponse:
        existing = db.query(User).filter(User.email == payload.email.lower()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="البريد الإلكتروني مسجل بالفعل، يرجى تسجيل الدخول"
            )

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

    @staticmethod
    def login_user(db: Session, payload: UserLoginRequest) -> TokenResponse:
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

    @staticmethod
    def get_current_user_profile(user: User) -> TokenResponse:
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

    @staticmethod
    def logout_user(token: str) -> None:
        revoke_token(token)
