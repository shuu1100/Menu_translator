"""Database package for SQLite, FTS5, and vector storage."""

from pathlib import Path
from backend.app.core.config import get_settings


def get_db_path() -> Path:
    """Return verified database path and ensure directory exists."""
    settings = get_settings()
    path = Path(settings.database_path)
    if not path.is_absolute():
        # Anchor relative to project root if running from backend/ or subfolder
        curr = Path(__file__).resolve()
        # curr is backend/app/db/__init__.py -> parent x 4 is workspace root
        workspace_root = curr.parent.parent.parent.parent
        candidate = workspace_root / path
        if candidate.parent.exists() or (workspace_root / "backend").exists():
            path = candidate
        else:
            path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
