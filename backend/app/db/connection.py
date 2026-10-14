"""Database connection manager with FTS5 and sqlite-vec support."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional
from backend.app.core.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db import get_db_path

logger = get_logger(__name__)


class DatabaseManager:
    """Manages SQLite connections, pragmas, and extension loading."""

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path
        self._vector_supported: Optional[bool] = None
        self._vector_version: Optional[str] = None
        self._vector_error: Optional[str] = None
        self._fts5_supported: Optional[bool] = None

    @property
    def db_path(self) -> Path:
        if self._db_path is None:
            self._db_path = get_db_path()
        return self._db_path

    def _configure_connection(self, con: sqlite3.Connection) -> None:
        """Apply required pragmas and load extensions."""
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON;")
        con.execute("PRAGMA busy_timeout = 5000;")
        try:
            con.execute("PRAGMA journal_mode = WAL;")
        except sqlite3.OperationalError:
            # In-memory or temporary databases might not support WAL mode
            pass

        # Load sqlite-vec extension if enabled
        settings = get_settings()
        if settings.sqlite_vec_enabled:
            try:
                import sqlite_vec

                con.enable_load_extension(True)
                sqlite_vec.load(con)
                con.enable_load_extension(False)
                if self._vector_supported is None:
                    ver = con.execute("SELECT vec_version()").fetchone()[0]
                    self._vector_supported = True
                    self._vector_version = str(ver)
                    logger.info("Loaded sqlite-vec extension successfully: %s", self._vector_version)
            except Exception as exc:
                self._vector_supported = False
                self._vector_error = str(exc)
                logger.warning(
                    "sqlite-vec extension could not be loaded; falling back to lexical-only FTS5 search: %s",
                    exc,
                )
        else:
            self._vector_supported = False
            self._vector_error = "sqlite_vec_enabled setting is False"

        # Check FTS5 support
        if self._fts5_supported is None:
            try:
                con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS _probe_fts USING fts5(x);")
                con.execute("DROP TABLE IF EXISTS _probe_fts;")
                self._fts5_supported = True
            except Exception as exc:
                self._fts5_supported = False
                logger.error("FTS5 extension is not available in SQLite: %s", exc)

    def create_connection(self) -> sqlite3.Connection:
        """Create and configure a new SQLite connection."""
        target_path = str(self.db_path)
        con = sqlite3.connect(target_path, timeout=10.0, check_same_thread=False)
        self._configure_connection(con)
        return con

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager yielding an active database connection with commit/rollback."""
        con = self.create_connection()
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic health status of database engine and extensions."""
        # Initialize probe if not yet called
        if self._vector_supported is None or self._fts5_supported is None:
            try:
                with self.connection():
                    pass
            except Exception as exc:
                return {
                    "connected": False,
                    "database_path": str(self.db_path),
                    "error": str(exc),
                    "fts5": False,
                    "vector_search": False,
                    "vector_status": "error",
                }

        vector_status = "active" if self._vector_supported else "fallback_lexical_only"
        return {
            "connected": True,
            "database_path": str(self.db_path),
            "fts5": bool(self._fts5_supported),
            "vector_search": bool(self._vector_supported),
            "vector_version": self._vector_version,
            "vector_status": vector_status,
            "vector_error": self._vector_error,
        }


# Global default manager singleton
_default_manager: Optional[DatabaseManager] = None


def get_db_manager(db_path: Optional[Path] = None) -> DatabaseManager:
    """Return shared or customized DatabaseManager instance."""
    global _default_manager
    if db_path is not None:
        return DatabaseManager(db_path=db_path)
    if _default_manager is None:
        _default_manager = DatabaseManager()
    return _default_manager
