"""Culinary knowledge ingestion service with row-level validation, deduplication,
and verified record preservation.
"""

import csv
import io
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field, ValidationError
from backend.app.core.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.connection import DatabaseManager, get_db_manager
from backend.app.db.models import (
    AllergenEvidenceRecord,
    DishIngredientRecord,
    DishRecord,
    RestaurantRecord,
)
from backend.app.services.embedding import (
    BaseEmbeddingProvider,
    get_embedding_provider,
    serialize_float32,
)

logger = get_logger(__name__)


class DishImportItem(BaseModel):
    """Schema for validating imported dish records."""

    dish_id: Optional[str] = None
    restaurant_id: Optional[str] = None
    native_name: str = Field(min_length=1)
    aliases: List[str] = Field(default_factory=list)
    phonetic_spelling: Optional[str] = None
    canonical_category: Optional[str] = None
    base_ingredients: List[str] = Field(default_factory=list)
    cooking_technique: Optional[str] = None
    cultural_narrative: Optional[str] = None
    flavor_profile: Optional[str] = None
    known_allergens: List[str] = Field(default_factory=list)
    dietary_flags: Dict[str, Any] = Field(default_factory=dict)
    price_metadata: Optional[Dict[str, Any]] = None
    provenance: str = Field(min_length=1)
    verification_status: str = Field(default="unverified", pattern="^(verified|unverified)$")
    ingredients: List[DishIngredientRecord] = Field(default_factory=list)
    allergen_evidence: List[AllergenEvidenceRecord] = Field(default_factory=list)


class IngestionSummary(BaseModel):
    """Summary of batch ingestion operation."""

    import_id: str
    source_name: str
    total_records: int
    inserted: int
    updated: int
    skipped: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class KnowledgeIngestionService:
    """Handles importing and indexing culinary knowledge from JSON and CSV."""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ):
        self.db_manager = db_manager or get_db_manager()
        self.embedding_provider = embedding_provider or get_embedding_provider()

    def _generate_dish_id(self, restaurant_id: Optional[str], native_name: str) -> str:
        """Generate stable deterministic ID for a dish."""
        raw = f"{restaurant_id or 'global'}_{native_name.strip().lower()}"
        clean = "".join(c if c.isalnum() else "_" for c in raw)
        return f"dish_{clean[:40]}_{abs(hash(raw)) % 1000000:06d}"

    def ingest_restaurants(self, restaurants: List[Dict[str, Any]]) -> IngestionSummary:
        """Ingest list of restaurant definitions."""
        import_id = f"import_rest_{uuid.uuid4().hex[:8]}"
        inserted = 0
        updated = 0
        errors: List[Dict[str, Any]] = []

        with self.db_manager.connection() as con:
            for idx, raw_rec in enumerate(restaurants, start=1):
                try:
                    rest = RestaurantRecord(**raw_rec)
                    cur = con.execute(
                        "SELECT restaurant_id FROM restaurants WHERE restaurant_id = ?",
                        (rest.restaurant_id,),
                    )
                    exists = cur.fetchone() is not None
                    if exists:
                        con.execute(
                            """
                            UPDATE restaurants
                            SET display_name = ?, locale = ?, location_label = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE restaurant_id = ?
                            """,
                            (rest.display_name, rest.locale, rest.location_label, rest.restaurant_id),
                        )
                        updated += 1
                    else:
                        con.execute(
                            """
                            INSERT INTO restaurants (restaurant_id, display_name, locale, location_label)
                            VALUES (?, ?, ?, ?)
                            """,
                            (rest.restaurant_id, rest.display_name, rest.locale, rest.location_label),
                        )
                        inserted += 1
                except (ValidationError, Exception) as exc:
                    errors.append({"row": idx, "identifier": str(raw_rec.get("restaurant_id")), "error": str(exc)})

        return IngestionSummary(
            import_id=import_id,
            source_name="restaurants_import",
            total_records=len(restaurants),
            inserted=inserted,
            updated=updated,
            skipped=len(errors),
            errors=errors,
        )

    def ingest_dishes(
        self,
        raw_items: List[Dict[str, Any]],
        source_name: str = "batch_import",
        allow_overwrite_verified: bool = False,
    ) -> IngestionSummary:
        """Ingest, validate, deduplicate, and vector-index a list of dish items."""
        import_id = f"import_{uuid.uuid4().hex[:8]}"
        inserted = 0
        updated = 0
        skipped = 0
        errors: List[Dict[str, Any]] = []

        status = self.db_manager.get_status()
        vector_enabled = status.get("vector_search", False)

        with self.db_manager.connection() as con:
            for idx, raw in enumerate(raw_items, start=1):
                # 1. Validation
                try:
                    item = DishImportItem(**raw)
                except ValidationError as ve:
                    errors.append({
                        "row": idx,
                        "identifier": str(raw.get("native_name", f"row_{idx}")),
                        "error": str(ve),
                    })
                    skipped += 1
                    continue

                dish_id = item.dish_id or self._generate_dish_id(item.restaurant_id, item.native_name)

                # Ensure referenced restaurant exists to satisfy foreign key constraint
                if item.restaurant_id:
                    con.execute(
                        "INSERT OR IGNORE INTO restaurants (restaurant_id, display_name, locale) VALUES (?, ?, 'und')",
                        (item.restaurant_id, item.restaurant_id),
                    )

                # 2. Check existing record
                cur = con.execute(
                    "SELECT dish_id, verification_status FROM dishes WHERE dish_id = ?",
                    (dish_id,),
                )
                existing = cur.fetchone()

                # Deduplication check by (restaurant_id, native_name) if not found by dish_id
                if not existing:
                    cur_dup = con.execute(
                        """
                        SELECT dish_id, verification_status FROM dishes 
                        WHERE native_name = ? AND (restaurant_id = ? OR (restaurant_id IS NULL AND ? IS NULL))
                        """,
                        (item.native_name, item.restaurant_id, item.restaurant_id),
                    )
                    existing = cur_dup.fetchone()
                    if existing:
                        dish_id = existing["dish_id"]

                # 3. Policy: Do not overwrite verified record with unverified import
                if existing:
                    existing_status = existing["verification_status"]
                    if existing_status == "verified" and item.verification_status == "unverified" and not allow_overwrite_verified:
                        skipped += 1
                        errors.append({
                            "row": idx,
                            "identifier": dish_id,
                            "error": f"Skipped: cannot overwrite verified record '{dish_id}' with unverified import data without explicit policy",
                        })
                        continue

                    # Update record
                    con.execute(
                        """
                        UPDATE dishes SET
                            restaurant_id = ?,
                            native_name = ?,
                            aliases = ?,
                            phonetic_spelling = ?,
                            canonical_category = ?,
                            base_ingredients = ?,
                            cooking_technique = ?,
                            cultural_narrative = ?,
                            flavor_profile = ?,
                            known_allergens = ?,
                            dietary_flags = ?,
                            price_metadata = ?,
                            provenance = ?,
                            verification_status = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE dish_id = ?
                        """,
                        (
                            item.restaurant_id,
                            item.native_name,
                            json.dumps(item.aliases, ensure_ascii=False),
                            item.phonetic_spelling,
                            item.canonical_category,
                            json.dumps(item.base_ingredients, ensure_ascii=False),
                            item.cooking_technique,
                            item.cultural_narrative,
                            item.flavor_profile,
                            json.dumps(item.known_allergens, ensure_ascii=False),
                            json.dumps(item.dietary_flags, ensure_ascii=False),
                            json.dumps(item.price_metadata, ensure_ascii=False) if item.price_metadata else None,
                            item.provenance,
                            item.verification_status,
                            dish_id,
                        ),
                    )
                    # Clear child records to replace
                    con.execute("DELETE FROM dish_ingredients WHERE dish_id = ?", (dish_id,))
                    con.execute("DELETE FROM allergen_evidence WHERE dish_id = ?", (dish_id,))
                    updated += 1
                else:
                    # Insert record
                    con.execute(
                        """
                        INSERT INTO dishes (
                            dish_id, restaurant_id, native_name, aliases, phonetic_spelling,
                            canonical_category, base_ingredients, cooking_technique,
                            cultural_narrative, flavor_profile, known_allergens, dietary_flags,
                            price_metadata, provenance, verification_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            dish_id,
                            item.restaurant_id,
                            item.native_name,
                            json.dumps(item.aliases, ensure_ascii=False),
                            item.phonetic_spelling,
                            item.canonical_category,
                            json.dumps(item.base_ingredients, ensure_ascii=False),
                            item.cooking_technique,
                            item.cultural_narrative,
                            item.flavor_profile,
                            json.dumps(item.known_allergens, ensure_ascii=False),
                            json.dumps(item.dietary_flags, ensure_ascii=False),
                            json.dumps(item.price_metadata, ensure_ascii=False) if item.price_metadata else None,
                            item.provenance,
                            item.verification_status,
                        ),
                    )
                    inserted += 1

                # 4. Insert normalized ingredients
                for ing in item.ingredients:
                    con.execute(
                        """
                        INSERT INTO dish_ingredients (dish_id, name, quantity, unit, source, verification_status)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (dish_id, ing.name, ing.quantity, ing.unit, ing.source, ing.verification_status),
                    )

                # 5. Insert allergen evidence
                for all_ev in item.allergen_evidence:
                    con.execute(
                        """
                        INSERT INTO allergen_evidence (dish_id, allergen, status, evidence_source, reviewer_metadata)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (dish_id, all_ev.allergen, all_ev.status, all_ev.evidence_source, all_ev.reviewer_metadata),
                    )

                # 6. Dense Vector Indexing (sqlite-vec)
                if vector_enabled:
                    try:
                        embed_text = f"{item.native_name} {' '.join(item.aliases)} {' '.join(item.base_ingredients)} {item.cultural_narrative or ''}"
                        vec = self.embedding_provider.embed_text(embed_text)
                        vec_bytes = serialize_float32(vec)
                        con.execute("DELETE FROM vec_dishes WHERE dish_id = ?", (dish_id,))
                        con.execute(
                            "INSERT INTO vec_dishes (dish_id, embedding) VALUES (?, ?)",
                            (dish_id, vec_bytes),
                        )
                    except Exception as vec_exc:
                        logger.warning("Failed to index vector for dish '%s': %s", dish_id, vec_exc)

            # Record ingestion batch
            con.execute(
                """
                INSERT INTO knowledge_sources (import_id, source_name, record_count, status, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    import_id,
                    source_name,
                    inserted + updated,
                    "completed" if not errors else "partial",
                    json.dumps({"inserted": inserted, "updated": updated, "skipped": skipped, "errors_count": len(errors)}),
                ),
            )

        return IngestionSummary(
            import_id=import_id,
            source_name=source_name,
            total_records=len(raw_items),
            inserted=inserted,
            updated=updated,
            skipped=skipped,
            errors=errors,
        )

    def ingest_from_json_file(
        self,
        filepath: Union[str, Path],
        allow_overwrite_verified: bool = False,
    ) -> IngestionSummary:
        """Ingest culinary knowledge from a JSON file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"JSON knowledge file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            # Check if restaurants are provided
            if "restaurants" in data and isinstance(data["restaurants"], list):
                self.ingest_restaurants(data["restaurants"])
            items = data.get("dishes", [])
        elif isinstance(data, list):
            items = data
        else:
            raise ValueError("Expected JSON file to contain a list of dishes or an object with 'dishes' key.")

        return self.ingest_dishes(
            raw_items=items,
            source_name=path.name,
            allow_overwrite_verified=allow_overwrite_verified,
        )

    def ingest_from_csv_file(
        self,
        filepath: Union[str, Path],
        allow_overwrite_verified: bool = False,
    ) -> IngestionSummary:
        """Ingest culinary knowledge from a CSV file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"CSV knowledge file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            raw_items = []
            for row in reader:
                # Parse JSON or comma-separated fields
                aliases = []
                if row.get("aliases"):
                    try:
                        aliases = json.loads(row["aliases"])
                    except Exception:
                        aliases = [a.strip() for a in row["aliases"].split(",") if a.strip()]

                base_ingredients = []
                if row.get("base_ingredients"):
                    try:
                        base_ingredients = json.loads(row["base_ingredients"])
                    except Exception:
                        base_ingredients = [b.strip() for b in row["base_ingredients"].split(",") if b.strip()]

                known_allergens = []
                if row.get("known_allergens"):
                    try:
                        known_allergens = json.loads(row["known_allergens"])
                    except Exception:
                        known_allergens = [k.strip() for k in row["known_allergens"].split(",") if k.strip()]

                dietary_flags = {}
                if row.get("dietary_flags"):
                    try:
                        dietary_flags = json.loads(row["dietary_flags"])
                    except Exception:
                        dietary_flags = {}

                raw_items.append({
                    "dish_id": row.get("dish_id"),
                    "restaurant_id": row.get("restaurant_id") or None,
                    "native_name": row.get("native_name", ""),
                    "aliases": aliases,
                    "phonetic_spelling": row.get("phonetic_spelling"),
                    "canonical_category": row.get("canonical_category"),
                    "base_ingredients": base_ingredients,
                    "cooking_technique": row.get("cooking_technique"),
                    "cultural_narrative": row.get("cultural_narrative"),
                    "flavor_profile": row.get("flavor_profile"),
                    "known_allergens": known_allergens,
                    "dietary_flags": dietary_flags,
                    "provenance": row.get("provenance", f"csv_import_{path.name}"),
                    "verification_status": row.get("verification_status", "unverified"),
                })

        return self.ingest_dishes(
            raw_items=raw_items,
            source_name=path.name,
            allow_overwrite_verified=allow_overwrite_verified,
        )
