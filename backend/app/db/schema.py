"""Idempotent database schema, FTS5 virtual tables, and sqlite-vec initialization."""

import sqlite3
from typing import Optional
from backend.app.core.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.connection import DatabaseManager, get_db_manager

logger = get_logger(__name__)

INIT_SCHEMA_SQL = """
-- 1. Restaurants table
CREATE TABLE IF NOT EXISTS restaurants (
    restaurant_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    locale TEXT NOT NULL,
    location_label TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Dishes table
CREATE TABLE IF NOT EXISTS dishes (
    dish_id TEXT PRIMARY KEY,
    restaurant_id TEXT REFERENCES restaurants(restaurant_id) ON DELETE CASCADE,
    native_name TEXT NOT NULL,
    aliases TEXT,                 -- JSON array of alias strings
    phonetic_spelling TEXT,
    canonical_category TEXT,
    base_ingredients TEXT,        -- JSON array of ingredient strings
    cooking_technique TEXT,
    cultural_narrative TEXT,
    flavor_profile TEXT,
    known_allergens TEXT,         -- JSON array of allergen strings
    dietary_flags TEXT,           -- JSON object: {"is_vegan": bool, "is_vegetarian": bool, ...}
    price_metadata TEXT,          -- JSON object: {"amount": float, "currency": str}
    provenance TEXT NOT NULL,     -- Source identifier or documentation URL
    verification_status TEXT NOT NULL DEFAULT 'unverified', -- 'verified' or 'unverified'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Normalized dish ingredients table
CREATE TABLE IF NOT EXISTS dish_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dish_id TEXT NOT NULL REFERENCES dishes(dish_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    quantity TEXT,
    unit TEXT,
    source TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unverified'
);

-- 4. Allergen evidence table
CREATE TABLE IF NOT EXISTS allergen_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dish_id TEXT NOT NULL REFERENCES dishes(dish_id) ON DELETE CASCADE,
    allergen TEXT NOT NULL,
    status TEXT NOT NULL,         -- 'contains', 'may_contain', 'not_listed', 'unknown'
    evidence_source TEXT NOT NULL,
    reviewer_metadata TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Knowledge sources and import history table
CREATE TABLE IF NOT EXISTS knowledge_sources (
    import_id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    record_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'completed',
    metadata TEXT                 -- JSON metadata
);

-- Relational indexes
CREATE INDEX IF NOT EXISTS idx_dishes_restaurant ON dishes(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_dishes_native_name ON dishes(native_name);
CREATE INDEX IF NOT EXISTS idx_dish_ingredients_dish_id ON dish_ingredients(dish_id);
CREATE INDEX IF NOT EXISTS idx_allergen_evidence_dish_id ON allergen_evidence(dish_id);

-- 6. FTS5 Virtual Table for full-text lexical search
CREATE VIRTUAL TABLE IF NOT EXISTS dishes_fts USING fts5(
    dish_id UNINDEXED,
    native_name,
    aliases,
    base_ingredients,
    cultural_narrative
);

-- FTS5 synchronization triggers
DROP TRIGGER IF EXISTS trg_dishes_ai;
CREATE TRIGGER trg_dishes_ai AFTER INSERT ON dishes
BEGIN
    INSERT INTO dishes_fts(dish_id, native_name, aliases, base_ingredients, cultural_narrative)
    VALUES (
        new.dish_id,
        new.native_name,
        COALESCE(new.aliases, ''),
        COALESCE(new.base_ingredients, ''),
        COALESCE(new.cultural_narrative, '')
    );
END;

DROP TRIGGER IF EXISTS trg_dishes_ad;
CREATE TRIGGER trg_dishes_ad AFTER DELETE ON dishes
BEGIN
    DELETE FROM dishes_fts WHERE dish_id = old.dish_id;
END;

DROP TRIGGER IF EXISTS trg_dishes_au;
CREATE TRIGGER trg_dishes_au AFTER UPDATE ON dishes
BEGIN
    DELETE FROM dishes_fts WHERE dish_id = old.dish_id;
    INSERT INTO dishes_fts(dish_id, native_name, aliases, base_ingredients, cultural_narrative)
    VALUES (
        new.dish_id,
        new.native_name,
        COALESCE(new.aliases, ''),
        COALESCE(new.base_ingredients, ''),
        COALESCE(new.cultural_narrative, '')
    );
END;
"""


def init_database(db_manager: Optional[DatabaseManager] = None) -> None:
    """Initialize database tables, FTS5 virtual tables, and sqlite-vec virtual table idempotently."""
    manager = db_manager or get_db_manager()
    settings = get_settings()
    dimension = settings.embedding_dimension

    with manager.connection() as con:
        # Execute core schema
        con.executescript(INIT_SCHEMA_SQL)
        logger.info("Initialized core SQLite schema, relational indexes, and FTS5 tables successfully.")

        # Attempt to create sqlite-vec virtual table if supported
        status = manager.get_status()
        if status.get("vector_search", False):
            try:
                con.execute(
                    f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_dishes USING vec0("
                    f"dish_id text primary key, "
                    f"embedding float[{dimension}]"
                    f");"
                )
                logger.info(
                    "Initialized sqlite-vec table 'vec_dishes' with dimension %d.",
                    dimension,
                )
            except sqlite3.OperationalError as exc:
                logger.warning("Could not initialize vec_dishes virtual table: %s", exc)
        else:
            logger.info("Skipping vec_dishes creation (sqlite-vec extension is unavailable/disabled).")
