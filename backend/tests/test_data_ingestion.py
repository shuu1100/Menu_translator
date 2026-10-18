"""Tests for data ingestion service: row-level validation, deduplication, and verified record preservation."""

import json
import tempfile
from pathlib import Path
import pytest
from backend.app.db.connection import DatabaseManager
from backend.app.db.schema import init_database
from backend.app.services.rag.ingestion import KnowledgeIngestionService


@pytest.fixture
def fresh_ingestion():
    """Create fresh in-memory or temporary database for ingestion testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = Path(f.name)

    manager = DatabaseManager(db_path=temp_path)
    init_database(manager)
    service = KnowledgeIngestionService(db_manager=manager)
    yield service, manager

    if temp_path.exists():
        try:
            temp_path.unlink()
        except Exception:
            pass


def test_ingest_json_valid_records(fresh_ingestion):
    """Test importing records from valid demo JSON."""
    service, _ = fresh_ingestion
    demo_json = Path(__file__).resolve().parent.parent / "app" / "db" / "fixtures" / "demo_culinary_kb.json"
    summary = service.ingest_from_json_file(demo_json)
    assert summary.total_records > 0
    assert summary.inserted > 0
    assert summary.skipped == 0
    assert len(summary.errors) == 0


def test_ingest_csv_valid_records(fresh_ingestion):
    """Test importing records from valid demo CSV."""
    service, _ = fresh_ingestion
    demo_csv = Path(__file__).resolve().parent.parent / "app" / "db" / "fixtures" / "demo_culinary_kb.csv"
    summary = service.ingest_from_csv_file(demo_csv)
    assert summary.total_records == 3
    assert summary.inserted == 3
    assert summary.skipped == 0
    assert len(summary.errors) == 0


def test_ingest_row_level_validation_errors(fresh_ingestion):
    """Test that malformed records produce row-level errors and valid records are still ingested."""
    service, manager = fresh_ingestion
    mixed_batch = [
        {
            "dish_id": "good_dish_1",
            "native_name": "Valid Dish",
            "provenance": "test",
            "verification_status": "unverified",
        },
        {
            # Invalid: missing required native_name
            "dish_id": "bad_dish_2",
            "native_name": "",
            "provenance": "test",
            "verification_status": "unverified",
        },
        {
            # Invalid: verification_status not in ('verified', 'unverified')
            "dish_id": "bad_dish_3",
            "native_name": "Invalid Status Dish",
            "provenance": "test",
            "verification_status": "super_verified_invalid",
        },
        {
            "dish_id": "good_dish_4",
            "native_name": "Second Valid Dish",
            "provenance": "test",
            "verification_status": "verified",
        },
    ]

    summary = service.ingest_dishes(mixed_batch, source_name="test_mixed")
    assert summary.total_records == 4
    assert summary.inserted == 2
    assert summary.skipped == 2
    assert len(summary.errors) == 2
    # Ensure errors record row numbers
    assert summary.errors[0]["row"] == 2
    assert summary.errors[1]["row"] == 3


def test_ingest_preserves_verified_records_from_unverified_overwrite(fresh_ingestion):
    """Policy check: an incoming unverified record must NOT overwrite an existing verified record."""
    service, manager = fresh_ingestion

    # 1. Ingest verified dish
    initial = [
        {
            "dish_id": "dish_ramen_verified",
            "restaurant_id": "rest_1",
            "native_name": "豚骨ラーメン",
            "cultural_narrative": "Verified rich tonkotsu broth from certified chef.",
            "provenance": "verified_audit",
            "verification_status": "verified",
        }
    ]
    s1 = service.ingest_dishes(initial)
    assert s1.inserted == 1

    # 2. Attempt to overwrite with unverified import (allow_overwrite_verified=False)
    unverified_attempt = [
        {
            "dish_id": "dish_ramen_verified",
            "restaurant_id": "rest_1",
            "native_name": "豚骨ラーメン",
            "cultural_narrative": "Bogus crowdsourced change",
            "provenance": "random_unverified_import",
            "verification_status": "unverified",
        }
    ]
    s2 = service.ingest_dishes(unverified_attempt, allow_overwrite_verified=False)
    assert s2.skipped == 1
    assert len(s2.errors) == 1
    assert "cannot overwrite verified record" in s2.errors[0]["error"]

    # Verify original record unchanged
    with manager.connection() as con:
        row = con.execute("SELECT cultural_narrative, verification_status FROM dishes WHERE dish_id = 'dish_ramen_verified'").fetchone()
        assert row["verification_status"] == "verified"
        assert "Verified rich tonkotsu broth" in row["cultural_narrative"]


def test_ingest_allows_verified_overwrite_when_explicitly_enabled(fresh_ingestion):
    """Policy check: when allow_overwrite_verified=True, update proceeds."""
    service, manager = fresh_ingestion

    # 1. Verified record
    initial = [
        {
            "dish_id": "dish_target",
            "native_name": "Sample Dish",
            "cultural_narrative": "Original verified note",
            "provenance": "v1",
            "verification_status": "verified",
        }
    ]
    service.ingest_dishes(initial)

    # 2. Update with explicit permission
    update = [
        {
            "dish_id": "dish_target",
            "native_name": "Sample Dish",
            "cultural_narrative": "Updated note with override",
            "provenance": "v2",
            "verification_status": "unverified",
        }
    ]
    s2 = service.ingest_dishes(update, allow_overwrite_verified=True)
    assert s2.updated == 1
    assert s2.skipped == 0

    with manager.connection() as con:
        row = con.execute("SELECT cultural_narrative FROM dishes WHERE dish_id = 'dish_target'").fetchone()
        assert row["cultural_narrative"] == "Updated note with override"


def test_ingest_deduplication(fresh_ingestion):
    """Verify deduplication by (restaurant_id, native_name) when dish_id is not specified."""
    service, manager = fresh_ingestion
    record1 = {
        "restaurant_id": "rest_test",
        "native_name": "Pad Thai",
        "provenance": "batch1",
        "verification_status": "unverified",
        "cultural_narrative": "Initial description",
    }
    service.ingest_dishes([record1])

    # Second batch with same restaurant_id and native_name
    record2 = {
        "restaurant_id": "rest_test",
        "native_name": "Pad Thai",
        "provenance": "batch2",
        "verification_status": "verified",
        "cultural_narrative": "Updated and verified description",
    }
    s2 = service.ingest_dishes([record2])
    assert s2.updated == 1
    assert s2.inserted == 0

    with manager.connection() as con:
        rows = con.execute("SELECT dish_id, verification_status FROM dishes WHERE native_name = 'Pad Thai'").fetchall()
        assert len(rows) == 1
        assert rows[0]["verification_status"] == "verified"
