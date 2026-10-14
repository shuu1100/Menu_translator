"""Hybrid culinary knowledge retriever using SQLite, FTS5, sqlite-vec, and RRF."""

import json
import re
import sqlite3
from typing import Any, Dict, List, Optional, Set, Tuple
from backend.app.core.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.connection import DatabaseManager, get_db_manager
from backend.app.db.models import (
    AllergenEvidenceRecord,
    DishIngredientRecord,
    DishRecord,
    RetrievedDish,
)
from backend.app.services.embedding import (
    BaseEmbeddingProvider,
    get_embedding_provider,
    serialize_float32,
)

logger = get_logger(__name__)


def sanitize_fts5_query(query: str) -> str:
    """Sanitize user-provided text for safe FTS5 MATCH queries."""
    # Extract alphanumeric words and unicode words (Japanese, Chinese, Arabic, etc.)
    tokens = re.findall(r"[\w]+|[\u4e00-\u9fff]+|[\u3040-\u309f]+|[\u30a0-\u30ff]+|[\u0600-\u06ff]+", query)
    if not tokens:
        return ""
    # Wrap each non-empty token in quotes to prevent FTS5 syntax errors
    clean_tokens = [f'"{tok}"' for tok in tokens if tok.strip()]
    return " OR ".join(clean_tokens)


class CulinaryRetriever:
    """Hybrid RAG retriever combining exact matching, FTS5 lexical search,
    sqlite-vec dense vector search, and Reciprocal Rank Fusion (RRF).
    """

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        k: Optional[int] = None,
        confidence_threshold: Optional[float] = None,
        max_vector_distance: float = 1.15,
    ):
        settings = get_settings()
        self.db_manager = db_manager or get_db_manager()
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.k = k if k is not None else settings.rrf_k
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else settings.retrieval_confidence_threshold
        )
        self.max_vector_distance = max_vector_distance

    def _is_accessible_to_restaurant(
        self, dish_restaurant_id: Optional[str], target_restaurant_id: Optional[str]
    ) -> bool:
        """Enforce strict restaurant isolation.
        
        - If target_restaurant_id is provided: dish must belong to that restaurant OR be a public dish (None).
        - If target_restaurant_id is NOT provided: dish MUST be public (None). Never leak private dishes.
        """
        if target_restaurant_id is not None:
            return dish_restaurant_id is None or dish_restaurant_id == target_restaurant_id
        return dish_restaurant_id is None

    def _search_exact_and_aliases(
        self, con: sqlite3.Connection, query: str, restaurant_id: Optional[str]
    ) -> List[str]:
        """Search exact native name and aliases."""
        clean_q = query.strip()
        if not clean_q:
            return []

        # Find dishes where native_name matches exactly (case-insensitive)
        cursor = con.execute(
            "SELECT dish_id, restaurant_id, aliases FROM dishes WHERE native_name = ? COLLATE NOCASE",
            (clean_q,),
        )
        matched_ids: List[str] = []
        for row in cursor.fetchall():
            if self._is_accessible_to_restaurant(row["restaurant_id"], restaurant_id):
                matched_ids.append(row["dish_id"])

        # Also inspect aliases JSON
        cursor_all = con.execute("SELECT dish_id, restaurant_id, aliases FROM dishes WHERE aliases IS NOT NULL")
        for row in cursor_all.fetchall():
            if row["dish_id"] in matched_ids:
                continue
            if not self._is_accessible_to_restaurant(row["restaurant_id"], restaurant_id):
                continue
            try:
                aliases_data = json.loads(row["aliases"]) if row["aliases"] else []
                if isinstance(aliases_data, list):
                    for alias in aliases_data:
                        if isinstance(alias, str) and alias.strip().lower() == clean_q.lower():
                            matched_ids.append(row["dish_id"])
                            break
            except Exception:
                continue

        return matched_ids

    def _search_fts5(
        self, con: sqlite3.Connection, query: str, restaurant_id: Optional[str], limit: int = 20
    ) -> List[str]:
        """Perform FTS5 BM25 lexical search."""
        sanitized = sanitize_fts5_query(query)
        if not sanitized:
            return []

        try:
            sql = """
                SELECT f.dish_id, d.restaurant_id, rank
                FROM dishes_fts f
                JOIN dishes d ON f.dish_id = d.dish_id
                WHERE dishes_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """
            cursor = con.execute(sql, (sanitized, limit * 2))
            ranked_ids: List[str] = []
            for row in cursor.fetchall():
                if self._is_accessible_to_restaurant(row["restaurant_id"], restaurant_id):
                    ranked_ids.append(row["dish_id"])
                if len(ranked_ids) >= limit:
                    break
            return ranked_ids
        except sqlite3.OperationalError as exc:
            logger.warning("FTS5 query failed for '%s': %s", query, exc)
            return []

    def _search_vector(
        self, con: sqlite3.Connection, query: str, restaurant_id: Optional[str], limit: int = 20
    ) -> List[str]:
        """Perform sqlite-vec dense vector similarity search if available."""
        status = self.db_manager.get_status()
        if not status.get("vector_search", False):
            return []

        try:
            query_vector = self.embedding_provider.embed_text(query)
            query_bytes = serialize_float32(query_vector)
            k_candidates = limit * 3

            sql = """
                SELECT v.dish_id, v.distance, d.restaurant_id
                FROM (
                    SELECT dish_id, distance
                    FROM vec_dishes
                    WHERE embedding MATCH ? AND k = ?
                ) v
                JOIN dishes d ON v.dish_id = d.dish_id
                ORDER BY v.distance
            """
            cursor = con.execute(sql, (query_bytes, k_candidates))
            ranked_ids: List[str] = []
            for row in cursor.fetchall():
                if row["distance"] > self.max_vector_distance:
                    continue
                if self._is_accessible_to_restaurant(row["restaurant_id"], restaurant_id):
                    ranked_ids.append(row["dish_id"])
                if len(ranked_ids) >= limit:
                    break
            return ranked_ids
        except Exception as exc:
            logger.warning("Dense vector search failed: %s", exc)
            return []

    def _hydrate_dish(self, con: sqlite3.Connection, dish_id: str) -> Optional[DishRecord]:
        """Load complete dish record with ingredients and allergen evidence."""
        cur = con.execute("SELECT * FROM dishes WHERE dish_id = ?", (dish_id,))
        row = cur.fetchone()
        if not row:
            return None

        # Parse JSON fields safely
        aliases = []
        if row["aliases"]:
            try:
                aliases = json.loads(row["aliases"])
            except Exception:
                aliases = [row["aliases"]]

        base_ingredients = []
        if row["base_ingredients"]:
            try:
                base_ingredients = json.loads(row["base_ingredients"])
            except Exception:
                base_ingredients = [row["base_ingredients"]]

        known_allergens = []
        if row["known_allergens"]:
            try:
                known_allergens = json.loads(row["known_allergens"])
            except Exception:
                known_allergens = [row["known_allergens"]]

        dietary_flags = {}
        if row["dietary_flags"]:
            try:
                dietary_flags = json.loads(row["dietary_flags"])
            except Exception:
                dietary_flags = {}

        price_metadata = None
        if row["price_metadata"]:
            try:
                price_metadata = json.loads(row["price_metadata"])
            except Exception:
                price_metadata = {"raw": row["price_metadata"]}

        # Ingredients
        cur_ing = con.execute("SELECT * FROM dish_ingredients WHERE dish_id = ?", (dish_id,))
        ingredients = [
            DishIngredientRecord(
                id=i["id"],
                dish_id=i["dish_id"],
                name=i["name"],
                quantity=i["quantity"],
                unit=i["unit"],
                source=i["source"],
                verification_status=i["verification_status"],
            )
            for i in cur_ing.fetchall()
        ]

        # Allergen evidence
        cur_all = con.execute("SELECT * FROM allergen_evidence WHERE dish_id = ?", (dish_id,))
        allergen_evidence = [
            AllergenEvidenceRecord(
                id=a["id"],
                dish_id=a["dish_id"],
                allergen=a["allergen"],
                status=a["status"],
                evidence_source=a["evidence_source"],
                reviewer_metadata=a["reviewer_metadata"],
                updated_at=str(a["updated_at"]) if a["updated_at"] else None,
            )
            for a in cur_all.fetchall()
        ]

        return DishRecord(
            dish_id=row["dish_id"],
            restaurant_id=row["restaurant_id"],
            native_name=row["native_name"],
            aliases=aliases,
            phonetic_spelling=row["phonetic_spelling"],
            canonical_category=row["canonical_category"],
            base_ingredients=base_ingredients,
            cooking_technique=row["cooking_technique"],
            cultural_narrative=row["cultural_narrative"],
            flavor_profile=row["flavor_profile"],
            known_allergens=known_allergens,
            dietary_flags=dietary_flags,
            price_metadata=price_metadata,
            provenance=row["provenance"],
            verification_status=row["verification_status"],
            created_at=str(row["created_at"]) if row["created_at"] else None,
            updated_at=str(row["updated_at"]) if row["updated_at"] else None,
            ingredients=ingredients,
            allergen_evidence=allergen_evidence,
        )

    def retrieve_dish(
        self,
        dish_name: str,
        restaurant_id: Optional[str] = None,
        limit: int = 5,
    ) -> Optional[RetrievedDish]:
        """Retrieve authoritative dish context using hybrid RAG with RRF.
        
        Returns the top matching RetrievedDish if confidence meets threshold,
        or None if no match meets the threshold.
        """
        results = self.retrieve_candidates(dish_name, restaurant_id=restaurant_id, limit=limit)
        if results and results[0].is_authoritative:
            return results[0]
        return None

    def retrieve_candidates(
        self,
        query: str,
        restaurant_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[RetrievedDish]:
        """Perform full hybrid retrieval returning ranked candidates with RRF scores."""
        clean_q = query.strip()
        if not clean_q:
            return []

        with self.db_manager.connection() as con:
            # 1. Exact match
            exact_ids = set(self._search_exact_and_aliases(con, clean_q, restaurant_id))

            # 2. FTS5 Lexical search
            fts_ids = self._search_fts5(con, clean_q, restaurant_id, limit=limit * 2)

            # 3. Dense Vector search
            vec_ids = self._search_vector(con, clean_q, restaurant_id, limit=limit * 2)

            # 4. Reciprocal Rank Fusion (RRF)
            # RRF score = sum(1 / (k + rank))
            all_candidate_ids: Set[str] = exact_ids.union(fts_ids).union(vec_ids)
            if not all_candidate_ids:
                return []

            rrf_scores: Dict[str, float] = {}
            lexical_ranks: Dict[str, int] = {}
            vector_ranks: Dict[str, int] = {}

            # Lexical ranks
            for rank_idx, d_id in enumerate(fts_ids, start=1):
                lexical_ranks[d_id] = rank_idx
                rrf_scores[d_id] = rrf_scores.get(d_id, 0.0) + (1.0 / (self.k + rank_idx))

            # Vector ranks
            for rank_idx, d_id in enumerate(vec_ids, start=1):
                vector_ranks[d_id] = rank_idx
                rrf_scores[d_id] = rrf_scores.get(d_id, 0.0) + (1.0 / (self.k + rank_idx))

            # Exact match boost
            for d_id in exact_ids:
                # Exact match receives top rank boost
                rrf_scores[d_id] = rrf_scores.get(d_id, 0.0) + (1.0 / (self.k + 1))

            # Sort descending by RRF score
            sorted_candidates = sorted(
                all_candidate_ids, key=lambda did: rrf_scores.get(did, 0.0), reverse=True
            )

            # 5. Hydrate records
            retrieved_list: List[RetrievedDish] = []
            for d_id in sorted_candidates[:limit]:
                dish_rec = self._hydrate_dish(con, d_id)
                if not dish_rec:
                    continue

                score = rrf_scores.get(d_id, 0.0)
                is_exact = d_id in exact_ids
                lex_rank = lexical_ranks.get(d_id)
                vec_rank = vector_ranks.get(d_id)

                # Determine match type
                if is_exact and (lex_rank or vec_rank):
                    match_type = "hybrid"
                elif is_exact:
                    match_type = "exact"
                elif lex_rank and vec_rank:
                    match_type = "hybrid"
                elif lex_rank:
                    match_type = "fts"
                elif vec_rank:
                    match_type = "vector"
                else:
                    match_type = "unknown"

                is_authoritative = score >= self.confidence_threshold

                retrieved_list.append(
                    RetrievedDish(
                        dish=dish_rec,
                        rrf_score=round(score, 6),
                        lexical_rank=lex_rank,
                        vector_rank=vec_rank,
                        exact_match=is_exact,
                        match_type=match_type,
                        is_authoritative=is_authoritative,
                    )
                )

            return retrieved_list
