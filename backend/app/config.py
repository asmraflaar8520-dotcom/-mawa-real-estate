import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

PROJECT_NAME = os.getenv("PROJECT_NAME", "MA'WA | مأوى")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
SECRET_KEY = os.getenv("SECRET_KEY", "mawa_dev_super_secret_jwt_key_9283748291028374")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Check if running in a serverless environment (like Vercel) where root is read-only
IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("NOW_REGION"))

if IS_VERCEL:
    import shutil
    tmp_dir = Path("/tmp")
    tmp_db = tmp_dir / "mawa.db"
    orig_db = BASE_DIR / "mawa.db"
    if not tmp_db.exists() and orig_db.exists():
        try:
            shutil.copy2(orig_db, tmp_db)
        except Exception:
            pass
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{tmp_db.as_posix()}")
    STORAGE_PRIVATE_DIR = tmp_dir / "storage" / "private_docs"
    STORAGE_PUBLIC_DIR = tmp_dir / "storage" / "public_media"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR.as_posix()}/mawa.db")
    STORAGE_PRIVATE_DIR = Path(os.getenv("STORAGE_PRIVATE_DIR", BASE_DIR / "storage" / "private_docs"))
    STORAGE_PUBLIC_DIR = Path(os.getenv("STORAGE_PUBLIC_DIR", BASE_DIR / "storage" / "public_media"))

try:
    STORAGE_PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

if IS_VERCEL:
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

raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000,*")
ALLOWED_ORIGINS = [o.strip() for o in raw_origins.split(",") if o.strip()]
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))

