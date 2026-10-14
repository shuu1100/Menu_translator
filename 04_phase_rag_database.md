# Phase 4 Prompt --- Local Culinary Knowledge Base and Hybrid RAG

Implement a fully local, restaurant-scoped culinary knowledge base using
SQLite, FTS5, and sqlite-vec. This phase must not require a hosted
vector database.

## Database design

Create migrations or an idempotent initialization script for: -
`restaurants`: restaurant ID, display name, locale, optional location
label, created/updated timestamps. - `dishes`: stable dish ID,
restaurant ID, native name, aliases, phonetic spelling, canonical
category, base ingredients, cooking technique, cultural narrative,
flavor profile, known allergens, dietary flags, price metadata if
maintained, provenance/source, verification status, updated timestamp. -
`dish_ingredients`: normalized ingredient records, optional
quantity/unit, source, verification status. - `allergen_evidence`:
allergen, status (`contains`, `may_contain`, `not_listed`, `unknown`),
evidence source, reviewer/verification metadata, updated timestamp. -
Optional `menu_imports` / `knowledge_sources` to track source and update
provenance.

Use parameterized SQL and foreign keys. Use FTS5 over native names,
aliases, ingredients, and cultural narrative. Use sqlite-vec if its
extension is available and compatible; implement a graceful lexical-only
fallback with a clear health status. Do not silently claim vector search
is active if extension loading fails.

## Embeddings

Use a multilingual embedding model with a documented vector dimension;
configure it in one place and ensure `sqlite-vec` dimensions match. The
development plan shows 384-dimensional vectors, so if retaining that
schema, select and validate a compatible 384-dimensional embedding
model. If a different model is selected, migrate the schema instead of
truncating vectors. Store the embedding model ID/version in metadata.

Embed dish names, aliases, and useful ingredient/context text. Do not
embed sensitive/private recipe content into a third-party API; use local
embedding inference.

## Hybrid retrieval

For each extracted dish: 1. Search exact native name and aliases. 2. Run
FTS5 lexical search. 3. Run dense vector similarity search when
available. 4. Combine ranked results with Reciprocal Rank Fusion (RRF),
using `k=60` as the initial constant. 5. Filter by `restaurant_id` when
provided; never mix one restaurant's private recipe into another
restaurant's response. 6. Return top-k records with IDs,
source/provenance, score components, and verification status. 7. If
retrieval confidence is low, return no authoritative match and mark
context as unknown rather than forcing a false match.

Create a `CulinaryRetriever` service with deterministic tests for exact
match, alias match, transliteration variation, semantic match, no-match,
cross-restaurant isolation, and vector-extension-unavailable fallback.

## Data ingestion

Support a documented JSON/CSV import process. Validate rows, reject
malformed records with row-level errors, deduplicate carefully, preserve
source provenance, and never overwrite a verified record with an
unverified import without explicit policy. Include small fictional demo
records only; do not present fictional recipes as real restaurant facts.

## Acceptance criteria

-   Database initializes on a clean install.
-   FTS5 retrieval works.
-   Dense search works if sqlite-vec is installed; fallback is explicit
    if not.
-   RRF combines results deterministically.
-   Restaurant isolation tests pass.
-   Retrieved evidence is returned to the enrichment service. Stop after
    Phase 4.
