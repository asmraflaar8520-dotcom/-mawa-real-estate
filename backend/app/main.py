import os
from pathlib import Path
from fastapi import FastAPI, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from backend.app.config import (
    PROJECT_NAME, ALLOWED_ORIGINS, STORAGE_PUBLIC_DIR, BASE_DIR, DATABASE_URL
)
from backend.app.database import engine, Base, SessionLocal, get_db
from backend.app.models.entities import User, Property, UserRole, IdentityStatus, ProfessionalStatus
from backend.app.security.auth_guard import hash_password
from backend.app.routes import auth, properties, contacts, verifications, admin, reports

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        return response

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize all database tables (supports SQLite & Supabase PostgreSQL)
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        import logging
        logging.getLogger("uvicorn.error").warning(f"[MA'WA Database Initialization] {e}")
    yield

app = FastAPI(
    title=PROJECT_NAME,
    description="منصة مأوى العقارية لمحافظة الغربية — مكانك يبدأ بثقة",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False
)

# Apply Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API Routers (Mount at both /api/... and /... for seamless Vercel & local compatibility)
routers_to_mount = [
    (auth.router, "/auth"),
    (properties.router, "/properties"),
    (contacts.router, "/contact-requests"),
    (verifications.router, "/verifications"),
    (admin.router, "/admin"),
    (reports.router, "/reports"),
]

for r, path in routers_to_mount:
    app.include_router(r, prefix=f"/api{path}")
    app.include_router(r, prefix=path)

@app.get("/")
@app.get("/api")
@app.get("/health")
@app.get("/api/health")
def health(request: Request, db: Session = Depends(get_db)):
    try:
        db_type = "postgresql" if "postgres" in DATABASE_URL else "sqlite"
        prop_count = db.query(Property).count()
    except Exception as e:
        db_type = f"error: {str(e)}"
        prop_count = 0
    return {
        "status": "ok",
        "app": PROJECT_NAME,
        "database": db_type,
        "properties_count": prop_count,
        "path": request.url.path
    }


# Mount Public Media (Photos with EXIF stripped)
if STORAGE_PUBLIC_DIR.exists():
    app.mount("/media", StaticFiles(directory=str(STORAGE_PUBLIC_DIR)), name="media")

# Mount Frontend Static Assets (Locally when not running on Vercel CDN)
from backend.app.config import IS_VERCEL
frontend_dir = BASE_DIR / "frontend"
if not IS_VERCEL and frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


