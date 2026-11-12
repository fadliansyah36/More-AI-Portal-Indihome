"""Vercel Python Function entrypoint for the MoreAI FastAPI application."""
from pathlib import Path
import sys

_ENTRYPOINT = Path(__file__).resolve()
_API_ROOT = next(
    (
        candidate
        for parent in _ENTRYPOINT.parents
        for candidate in (parent, parent / "apps" / "api")
        if (candidate / "app" / "main.py").is_file()
    ),
    None,
)
if _API_ROOT is None:
    raise RuntimeError("moreai_api_workspace_root_not_found")

_REPOSITORY_ROOT = next(
    (
        candidate
        for candidate in (_API_ROOT, *_API_ROOT.parents)
        if (candidate / "engine").is_dir()
    ),
    _API_ROOT,
)

for _path in (str(_REPOSITORY_ROOT), str(_API_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from app.main import app  # noqa: E402

__all__ = ["app"]
