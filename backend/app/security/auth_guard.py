from datetime import datetime, timedelta, timezone
from typing import Optional, List
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status, Header, Cookie
from sqlalchemy.orm import Session
from backend.app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.app.database import get_db
from backend.app.models.entities import User, UserRole, IdentityStatus, ProfessionalStatus

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now_utc})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_token_from_header_or_cookie(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
) -> Optional[str]:
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ")[1]
    if access_token:
        return access_token
    return None

def get_current_user(
    token: Optional[str] = Depends(get_token_from_header_or_cookie),
    db: Session = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="جلسة غير مسجلة، يرجى تسجيل الدخول",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="رمز جلسة غير صالح")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="رمز الجلسة منتهي أو غير صالح")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="المستخدم غير موجود")
    if user.is_suspended:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="تم تعليق هذا الحساب لمخالفته المعايير")
    return user

def get_current_user_optional(
    token: Optional[str] = Depends(get_token_from_header_or_cookie),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            return None
        user = db.query(User).filter(User.id == user_id).first()
        if user and not user.is_suspended:
            return user
        return None
    except Exception:
        return None

def require_role(*roles: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ليس لديك الصلاحية الكافية للوصول لهذا الإجراء"
            )
        return current_user
    return role_checker

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="يتطلب هذا الإجراء صلاحيات إدارة عليا"
        )
    return current_user
