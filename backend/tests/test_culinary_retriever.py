"""Comprehensive tests for CulinaryRetriever covering exact match, aliases, transliteration,
vector semantic search, RRF scoring, restaurant isolation, and graceful fallback.
"""

import tempfile
from pathlib import Path
import pytest
from backend.app.db.connection import DatabaseManager
from backend.app.db.schema import init_database
from backend.app.services.rag.ingestion import KnowledgeIngestionService
from backend.app.services.rag.retriever import CulinaryRetriever, sanitize_fts5_query


@pytest.fixture
def populated_retriever():
    """Create a temporary database populated with the standard demo dataset."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = Path(f.name)

    manager = DatabaseManager(db_path=temp_path)
    init_database(manager)

    demo_json = Path(__file__).resolve().parent.parent / "app" / "db" / "fixtures" / "demo_culinary_kb.json"
    ingestion = KnowledgeIngestionService(db_manager=manager)
    ingestion.ingest_from_json_file(demo_json)

    retriever = CulinaryRetriever(db_manager=manager)
    yield retriever

    if temp_path.exists():
        try:
            temp_path.unlink()
        except Exception:
            pass


def test_sanitize_fts5_query():
    """Verify FTS5 query sanitizer wraps tokens in quotes and handles special characters."""
    assert sanitize_fts5_query('Tonkotsu "Ramen" (Special)') == '"Tonkotsu" OR "Ramen" OR "Special"'
    assert sanitize_fts5_query("醤油ラーメン") == '"醤油ラーメン"'
    assert sanitize_fts5_query("   ") == ""
    assert sanitize_fts5_query("فلافل") == '"فلافل"'


def test_retriever_exact_match(populated_retriever):
    """Test exact native script match retrieval."""
    match = populated_retriever.retrieve_dish("醤油ラーメン", restaurant_id="rest_sakura_tokyo")
    assert match is not None
    assert match.dish.dish_id == "dish_sakura_shoyu_ramen"
    assert match.exact_match is True
    assert match.is_authoritative is True
    assert match.dish.verification_status == "verified"
    assert "gluten" in [a.allergen for a in match.dish.allergen_evidence]


def test_retriever_alias_match(populated_retriever):
    """Test alias matching (e.g. 'Carbonara' matches 'Spaghetti alla Carbonara')."""
    match = populated_retriever.retrieve_dish("Carbonara", restaurant_id="rest_trattoria_roma")
    assert match is not None
    assert match.dish.dish_id == "dish_trattoria_carbonara"
    assert match.dish.native_name == "Spaghetti alla Carbonara"
    assert match.is_authoritative is True


def test_retriever_transliteration_variation(populated_retriever):
    """Test transliteration and phonetic variation query (e.g. 'Shoyu Ramen')."""
    match = populated_retriever.retrieve_dish("Shoyu Ramen", restaurant_id="rest_sakura_tokyo")
    assert match is not None
    assert match.dish.dish_id == "dish_sakura_shoyu_ramen"
    assert match.is_authoritative is True


def test_retriever_vector_semantic_match(populated_retriever):
    """Test semantic search when lexical text differs slightly."""
    # Query with semantic ingredients
    match = populated_retriever.retrieve_dish("fermented red miso broth noodles", restaurant_id="rest_sakura_tokyo")
    assert match is not None
    assert match.dish.dish_id == "dish_sakura_miso_ramen"


def test_retriever_no_match_returns_none(populated_retriever):
    """Test that unrelated query returns None and does not hallucinate false matches."""
    match = populated_retriever.retrieve_dish("Quantum_Flux_Pineapple_Pizza_12345", restaurant_id="rest_sakura_tokyo")
    assert match is None


def test_cross_restaurant_isolation_enforced(populated_retriever):
    """Strictly verify that private recipes are NEVER exposed across restaurants or unscoped queries."""
    # 1. Sakura's private soup is accessible to Sakura Noodle House
    sakura_match = populated_retriever.retrieve_dish("秘伝特製豚骨スープ", restaurant_id="rest_sakura_tokyo")
    assert sakura_match is not None
    assert sakura_match.dish.dish_id == "dish_sakura_secret_pork_tonkotsu"

    # 2. Sakura's private soup is strictly BLOCKED for Trattoria Da Marco
    trattoria_match = populated_retriever.retrieve_dish("秘伝特製豚骨スープ", restaurant_id="rest_trattoria_roma")
    assert trattoria_match is None

    # 3. Sakura's private soup is strictly BLOCKED for unscoped general search
    unscoped_match = populated_retriever.retrieve_dish("秘伝特製豚骨スープ", restaurant_id=None)
    assert unscoped_match is None

    # 4. Trattoria's private tiramisu is BLOCKED for Sakura Noodle House
    tiramisu_blocked = populated_retriever.retrieve_dish("Tiramisù della Nonna", restaurant_id="rest_sakura_tokyo")
    assert tiramisu_blocked is None

    # 5. Public global dish (Falafel) is accessible to ANY restaurant and unscoped search
    falafel_unscoped = populated_retriever.retrieve_dish("فلافل", restaurant_id=None)
    assert falafel_unscoped is not None
    assert falafel_unscoped.dish.dish_id == "dish_global_falafel"

    falafel_sakura = populated_retriever.retrieve_dish("فلافل", restaurant_id="rest_sakura_tokyo")
    assert falafel_sakura is not None
    assert falafel_sakura.dish.dish_id == "dish_global_falafel"


def test_rrf_scoring_determinism(populated_retriever):
    """Verify that Reciprocal Rank Fusion computes deterministic scores using k=60."""
    candidates = populated_retriever.retrieve_candidates("Spaghetti alla Carbonara", restaurant_id="rest_trattoria_roma")
    assert len(candidates) > 0
    top = candidates[0]
    # Exact match gets 1/(60+1) boost plus lexical/vector ranks
    assert top.rrf_score >= (1.0 / 61.0)
    assert top.exact_match is True
    # Ensure sorted in descending order of RRF score
    for i in range(len(candidates) - 1):
        assert candidates[i].rrf_score >= candidates[i + 1].rrf_score


def test_vector_extension_unavailable_fallback():
    """Verify graceful fallback to lexical-only search when vector extension is unavailable."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = Path(f.name)

    manager = DatabaseManager(db_path=temp_path)
    init_database(manager)

    demo_json = Path(__file__).resolve().parent.parent / "app" / "db" / "fixtures" / "demo_culinary_kb.json"
    ingestion = KnowledgeIngestionService(db_manager=manager)
    ingestion.ingest_from_json_file(demo_json)

    # Force vector search off in manager
    manager._vector_supported = False
    manager._vector_error = "Mocked vector extension unavailable"

    retriever = CulinaryRetriever(db_manager=manager)
    status = manager.get_status()
    assert status["vector_search"] is False
    assert status["vector_status"] == "fallback_lexical_only"

    # Exact and FTS search should still work seamlessly!
    match = retriever.retrieve_dish("醤油ラーメン", restaurant_id="rest_sakura_tokyo")
    assert match is not None
    assert match.dish.dish_id == "dish_sakura_shoyu_ramen"
    assert match.match_type in ["exact", "fts", "hybrid"]

    if temp_path.exists():
        try:
            temp_path.unlink()
        except Exception:
            pass
