import os
from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from backend.app.config import (
    PROJECT_NAME, ALLOWED_ORIGINS, STORAGE_PUBLIC_DIR, BASE_DIR
)
from backend.app.database import engine, Base, SessionLocal
from backend.app.models.entities import User, UserRole, IdentityStatus, ProfessionalStatus
from backend.app.security.auth_guard import hash_password
from backend.app.routes import auth, properties, contacts, verifications, admin, reports

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        return response

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize all database tables
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=PROJECT_NAME,
    description="منصة مأوى العقارية لمحافظة الغربية — مكانك يبدأ بثقة",
    version="1.0.0",
    lifespan=lifespan
)

# Apply Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(properties.router)
app.include_router(contacts.router)
app.include_router(verifications.router)
app.include_router(admin.router)
app.include_router(reports.router)

@app.get("/health")
def health():
    return {"status": "ok", "app": PROJECT_NAME}

# Mount Public Media (Photos with EXIF stripped)
if STORAGE_PUBLIC_DIR.exists():
    app.mount("/media", StaticFiles(directory=str(STORAGE_PUBLIC_DIR)), name="media")

# Mount Frontend Static Assets (Locally when not running on Vercel CDN)
from backend.app.config import IS_VERCEL
frontend_dir = BASE_DIR / "frontend"
if not IS_VERCEL and frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


