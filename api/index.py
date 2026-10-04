import sys
import os
from pathlib import Path

# Add project root to sys.path so 'backend' can be imported anywhere
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Mark serverless environment
os.environ.setdefault("VERCEL", "1")

from backend.app.main import app

# Expose app for Vercel
__all__ = ["app"]
