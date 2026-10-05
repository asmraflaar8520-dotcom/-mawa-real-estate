import os
import hashlib
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Set
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status, Header, Cookie, Request
from sqlalchemy.orm import Session
from backend.app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, IS_TESTING
from backend.app.database import get_db
from backend.app.models.entities import User, UserRole, IdentityStatus, ProfessionalStatus

# In-Memory Token Blacklist for Logouts
REVOKED_TOKENS: Set[str] = set()

def revoke_token(token: str) -> None:
    if token:
        REVOKED_TOKENS.add(token)

def is_token_revoked(token: str) -> bool:
    return token in REVOKED_TOKENS

# In-Memory Sliding-Window Rate Limiter
class InMemoryRateLimiter:
    def __init__(self):
        self._history = defaultdict(list)

    def check(self, key: str, max_requests: int = 15, window_seconds: int = 60, force: bool = False) -> bool:
        if IS_TESTING and not force and not os.getenv("TEST_RATE_LIMITING"):
            return True
        now = time.time()
        cutoff = now - window_seconds
        # Retain only timestamps within the sliding window
        self._history[key] = [t for t in self._history[key] if t > cutoff]
        if len(self._history[key]) >= max_requests:
            return False
        self._history[key].append(now)
        return True

rate_limiter = InMemoryRateLimiter()

def rate_limit(max_requests: int = 15, window_seconds: int = 60):
    def dependency(request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        key = f"{client_ip}:{request.url.path}"
        if not rate_limiter.check(key, max_requests=max_requests, window_seconds=window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="تم تجاوز الحد المسموح به من الطلبات مؤقتاً، يرجى المحاولة بعد قليل"
            )
    return dependency

def _normalize_password_bytes(password: str) -> bytes:
    pwd_bytes = password.encode('utf-8')
    if len(pwd_bytes) > 72:
        return hashlib.sha256(pwd_bytes).digest()[:72]
    return pwd_bytes

def hash_password(password: str) -> str:
    pwd_bytes = _normalize_password_bytes(password)
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # 1. Direct UTF-8 check (backward-compatible with existing seed data)
        raw_bytes = plain_password.encode('utf-8')
        if len(raw_bytes) <= 72 and bcrypt.checkpw(raw_bytes, hashed_password.encode('utf-8')):
            return True
        # 2. Normalized check for long or multi-byte passwords exceeding 72 bytes
        norm_bytes = _normalize_password_bytes(plain_password)
        return bcrypt.checkpw(norm_bytes, hashed_password.encode('utf-8'))
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
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="تم إنهاء هذه الجلسة، يرجى تسجيل الدخول مجدداً",
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
    if not token or is_token_revoked(token):
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
