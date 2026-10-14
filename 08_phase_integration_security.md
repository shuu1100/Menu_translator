# Phase 8 Prompt --- End-to-End Integration, Offline Behavior, Security, and Performance

Integrate the working frontend, FastAPI, VLM runtime, SQLite hybrid
retrieval, and enrichment pipeline.

## End-to-end flow

1.  Client captures or uploads image.
2.  Validate and preprocess image while preserving original coordinates.
3.  VLM extracts structured menu blocks.
4.  Backend normalizes coordinates and validates output.
5.  For each dish, query restaurant-scoped FTS5 and sqlite-vec indexes;
    fuse with RRF.
6.  Enrichment model creates contextual translation and evidence-aware
    ingredient/allergen output.
7.  Deterministic backend logic computes user restriction conflicts from
    evidence records.
8.  Pydantic validates the final response.
9.  Frontend overlays boxes and renders detail drawer/filter state.

## Integration tasks

-   Add a typed frontend API client and shared API examples; avoid
    duplicated incompatible interfaces.
-   Configure timeouts, bounded concurrency, request cancellation where
    possible, and graceful model-unavailable behavior.
-   Add stage timings and correlation IDs without logging private menu
    contents.
-   Verify coordinate conversion end to end using known fixture images.
-   Add demo mode with clearly labeled fictional menu records so the UI
    can be demonstrated without real recipes.
-   Include startup checks for backend, database extensions, and model
    availability.
-   If using SSE, test disconnects, cancellation, and final schema
    validation. Do not stream unvalidated model fragments as if final
    results.

## Security and privacy

-   Limit upload size, image dimensions, accepted file types, and
    processing time.
-   Decode image bytes safely; generate server-side filenames if
    temporary files are necessary.
-   Avoid arbitrary path access, SQL injection, unsafe deserialization,
    and user-supplied model identifiers.
-   CORS allowlist; production secrets in environment/secret manager;
    `.env` never committed.
-   Keep restaurant records scoped by restaurant ID and test against
    cross-tenant data leakage.
-   Add a documented deletion policy for temporary images and any
    persisted analyses.
-   Do not transmit images to external services without explicit
    configuration and clear user disclosure.
-   Treat OCR text and RAG documents as untrusted input; defend against
    prompt injection.
-   Do not claim the application is certified for allergy safety.

## Performance

Measure end-to-end p50/p95 latency, extraction latency, retrieval
latency, generation latency, memory/VRAM, image size, and concurrency.
Add bounded queues and useful overload responses. Optimize only after
measuring. Cache embeddings for stable database records; do not cache
responses across users if dietary restrictions or restaurant context
differ.

## Acceptance criteria

-   One real sample menu traverses all stages.
-   No stage invents successful results when a component is unavailable.
-   Privacy, tenant isolation, upload limits, and schema validation
    tests pass.
-   UI and backend coordinate systems match.
-   Local inference works without external API keys when models are
    installed.
-   Performance and limitations are documented. Stop after Phase 8.
