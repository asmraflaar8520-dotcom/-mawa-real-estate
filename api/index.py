import sys
import os
import traceback
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("VERCEL", "1")

error_trace = None
try:
    from backend.app.main import app
except Exception as e:
    error_trace = traceback.format_exc()
    app = FastAPI()

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    async def debug_error(full_path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Backend import failure on Vercel",
                "detail": str(error_trace)
            }
        )

__all__ = ["app"]
