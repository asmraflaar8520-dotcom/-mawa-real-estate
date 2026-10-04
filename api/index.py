import sys
import os
from pathlib import Path
from urllib.parse import parse_qs, urlencode

# Set project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure VERCEL environment is recognized
os.environ.setdefault("VERCEL", "1")

from backend.app.main import app as fastapi_app

class VercelPathMiddleware:
    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            query_string = scope.get("query_string", b"").decode("utf-8")
            if "_path=" in query_string:
                params = parse_qs(query_string, keep_blank_values=True)
                if "_path" in params:
                    raw_subpath = params.pop("_path")[0].strip("/")
                    # Reconstruct path as /api/{subpath}
                    scope["path"] = f"/api/{raw_subpath}" if raw_subpath else "/api"
                    scope["raw_path"] = scope["path"].encode("utf-8")
                    scope["query_string"] = urlencode(params, doseq=True).encode("utf-8")
        await self.inner_app(scope, receive, send)

app = VercelPathMiddleware(fastapi_app)

__all__ = ["app"]
