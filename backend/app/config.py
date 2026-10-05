import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# Security & Environment Validation
PROJECT_NAME = os.getenv("PROJECT_NAME", "MA'WA | مأوى")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
SECRET_KEY = os.getenv("SECRET_KEY", "mawa_prod_jwt_super_secret_key_9283748291028374_sec_key_2026")

if ENVIRONMENT.lower() == "production":
    if len(SECRET_KEY) < 32:
        raise ValueError(
            "CRITICAL SECURITY CONFIGURATION ERROR: A default or weak SECRET_KEY is not permitted in production! "
            "Set a cryptographically strong SECRET_KEY (minimum 32 characters) in your environment variables."
        )

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Check if running in a serverless environment (like Vercel) where root is read-only
IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("NOW_REGION"))
IS_TESTING = bool(os.getenv("TESTING") or os.getenv("PYTEST_CURRENT_TEST"))

if IS_TESTING:
    test_db = BASE_DIR / "test_mawa.db"
    db_env = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("SUPABASE_DB_URL") or f"sqlite:///{test_db.as_posix()}"
    if db_env.startswith("postgres://"):
        db_env = db_env.replace("postgres://", "postgresql://", 1)
    DATABASE_URL = db_env
    STORAGE_PRIVATE_DIR = BASE_DIR / "storage" / "test_private_docs"
    STORAGE_PUBLIC_DIR = BASE_DIR / "storage" / "test_public_media"
elif IS_VERCEL:
    import shutil
    tmp_dir = Path("/tmp")
    tmp_db = tmp_dir / "mawa.db"
    orig_db = BASE_DIR / "mawa.db"
    if not tmp_db.exists() and orig_db.exists():
        try:
            shutil.copy2(orig_db, tmp_db)
        except Exception:
            pass
    DEFAULT_SUPABASE_DB = "postgresql://postgres.yymozkjcxunutpiidfbt:Ashraf01024911243%2A%2A@aws-1-eu-central-1.pooler.supabase.com:6543/postgres"
    db_env = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("SUPABASE_DB_URL") or DEFAULT_SUPABASE_DB
    if db_env.startswith("postgres://"):
        db_env = db_env.replace("postgres://", "postgresql://", 1)
    DATABASE_URL = db_env
    STORAGE_PRIVATE_DIR = tmp_dir / "storage" / "private_docs"
    STORAGE_PUBLIC_DIR = tmp_dir / "storage" / "public_media"

    if DATABASE_URL.startswith("sqlite"):
        import logging
        logging.getLogger("uvicorn.error").warning(
            "[MA'WA PRODUCTION WARNING] Running SQLite on ephemeral serverless environment (Vercel). "
            "Data writes will not persist across container lifecycles. Set DATABASE_URL or POSTGRES_URL to a managed PostgreSQL database (e.g. Supabase / Neon)."
        )
else:
    db_env = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("SUPABASE_DB_URL") or f"sqlite:///{BASE_DIR.as_posix()}/mawa.db"
    if db_env.startswith("postgres://"):
        db_env = db_env.replace("postgres://", "postgresql://", 1)
    DATABASE_URL = db_env
    STORAGE_PRIVATE_DIR = Path(os.getenv("STORAGE_PRIVATE_DIR", BASE_DIR / "storage" / "private_docs"))
    STORAGE_PUBLIC_DIR = Path(os.getenv("STORAGE_PUBLIC_DIR", BASE_DIR / "storage" / "public_media"))

# Supabase Cloud Integration (Free Tier, No Credit Card Required)
SUPABASE_URL = (os.getenv("SUPABASE_URL") or "https://yymozkjcxunutpiidfbt.supabase.co").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or ""
SUPABASE_STORAGE_MEDIA_BUCKET = os.getenv("SUPABASE_STORAGE_MEDIA_BUCKET", "mawa-media")
SUPABASE_STORAGE_DOCS_BUCKET = os.getenv("SUPABASE_STORAGE_DOCS_BUCKET", "mawa-private-docs")
USE_SUPABASE_STORAGE = bool(SUPABASE_URL and SUPABASE_KEY and not IS_TESTING)

try:
    STORAGE_PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

if IS_VERCEL and not IS_TESTING:
    import shutil
    orig_public = BASE_DIR / "storage" / "public_media"
    if orig_public.exists():
        for f in orig_public.glob("*"):
            if f.is_file():
                dest = STORAGE_PUBLIC_DIR / f.name
                if not dest.exists():
                    try:
                        shutil.copy2(f, dest)
                    except Exception:
                        pass

# Default origins: Local development and production frontend domain without wildcard
raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000,https://mawa-real-estate.vercel.app"
)
# Ensure wildcard is removed to prevent browser credential rejections and CORS exploits
ALLOWED_ORIGINS = [o.strip() for o in raw_origins.split(",") if o.strip() and o.strip() != "*"]
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))

