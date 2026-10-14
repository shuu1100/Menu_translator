"""Unit tests for SQLite database initialization, FTS5 triggers, and health status."""

import tempfile
from pathlib import Path
import pytest
from backend.app.db.connection import DatabaseManager
from backend.app.db.schema import init_database
from backend.app.services.health_service import HealthService


@pytest.fixture
def temp_db():
    """Create a temporary database for test isolation."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = Path(f.name)
    manager = DatabaseManager(db_path=temp_path)
    init_database(manager)
    yield manager
    if temp_path.exists():
        try:
            temp_path.unlink()
        except Exception:
            pass


def test_database_initialization_idempotent(temp_db):
    """Verify that init_database creates all required tables and is safely idempotent."""
    # Run a second time to ensure idempotency
    init_database(temp_db)

    with temp_db.connection() as con:
        # Check core tables
        tables = [
            r[0]
            for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        assert "restaurants" in tables
        assert "dishes" in tables
        assert "dish_ingredients" in tables
        assert "allergen_evidence" in tables
        assert "knowledge_sources" in tables
        assert "dishes_fts" in tables


def test_fts5_synchronization_triggers(temp_db):
    """Verify that INSERT, UPDATE, and DELETE triggers keep dishes_fts synchronized."""
    with temp_db.connection() as con:
        # 1. Insert
        con.execute(
            """
            INSERT INTO dishes (dish_id, native_name, aliases, base_ingredients, cultural_narrative, provenance, verification_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("dish_test_1", "天ぷら蕎麦", "[\"Tempura Soba\"]", "[\"buckwheat noodles\", \"shrimp\"]", "Crisp tempura on warm soba", "test", "verified"),
        )
        fts_match = con.execute("SELECT dish_id FROM dishes_fts WHERE dishes_fts MATCH ?", ("天ぷら*",)).fetchall()
        assert len(fts_match) == 1
        assert fts_match[0]["dish_id"] == "dish_test_1"

        # 2. Update
        con.execute(
            "UPDATE dishes SET native_name = ? WHERE dish_id = ?",
            ("鴨南蛮蕎麦", "dish_test_1"),
        )
        old_match = con.execute("SELECT dish_id FROM dishes_fts WHERE dishes_fts MATCH ?", ("天ぷら*",)).fetchall()
        assert len(old_match) == 0
        new_match = con.execute("SELECT dish_id FROM dishes_fts WHERE dishes_fts MATCH ?", ("鴨南蛮*",)).fetchall()
        assert len(new_match) == 1
        assert new_match[0]["dish_id"] == "dish_test_1"

        # 3. Delete
        con.execute("DELETE FROM dishes WHERE dish_id = ?", ("dish_test_1",))
        deleted_match = con.execute("SELECT dish_id FROM dishes_fts WHERE dishes_fts MATCH ?", ("鴨南蛮*",)).fetchall()
        assert len(deleted_match) == 0


def test_database_manager_status_reporting(temp_db):
    """Verify DatabaseManager reports status without crashing."""
    status = temp_db.get_status()
    assert status["connected"] is True
    assert status["fts5"] is True
    assert "vector_search" in status
    assert "vector_status" in status
    assert status["vector_status"] in ["active", "fallback_lexical_only"]


@pytest.mark.asyncio
async def test_health_service_database_integration():
    """Verify HealthService.check_database correctly inspects the SQLite database."""
    health_service = HealthService()
    db_health = await health_service.check_database()
    assert db_health.status.value == "ok"
    assert db_health.details["connected"] is True
    assert db_health.details["fts5"] is True
    assert "dishes_count" in db_health.details
    assert "vector_status" in db_health.details
