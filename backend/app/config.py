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

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/mawa.db")

STORAGE_PRIVATE_DIR = Path(os.getenv("STORAGE_PRIVATE_DIR", BASE_DIR / "storage" / "private_docs"))
STORAGE_PUBLIC_DIR = Path(os.getenv("STORAGE_PUBLIC_DIR", BASE_DIR / "storage" / "public_media"))

STORAGE_PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")]
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))
