"""Vercel Python Function entrypoint for the MoreAI FastAPI application.

The Vercel project is rooted at the monorepo root. Add both the API
workspace and repository root explicitly so app and engine imports resolve
identically in local, CI, and Vercel function runtimes.
"""
from pathlib import Path
import sys

_API_ROOT = Path(__file__).resolve().parents[1]
_REPOSITORY_ROOT = _API_ROOT.parents[1]

for _path in (str(_REPOSITORY_ROOT), str(_API_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from app.main import app  # noqa: E402

__all__ = ["app"]
