# Phase 3 Prompt --- FastAPI Contracts and Pipeline Orchestration

Implement a stable API that joins image ingestion, extraction,
enrichment hooks, schema validation, and response delivery. Enrichment
can be stubbed with clearly marked test data until later phases; do not
fake a completed RAG integration.

## API

Version routes under `/api/v1`. - `GET /health`: application health. -
`GET /api/v1/health`: component health, including database and model
availability. - `POST /api/v1/menus/analyze`: multipart upload is
preferred for large images; optionally support base64 only if needed for
compatibility with the design document. -
`GET /api/v1/config/languages`: supported target-language list. -
Optional `GET /api/v1/menus/{analysis_id}` only if persistence is
implemented in a later phase.

Request fields: - image file - `target_language` enum: `en`, `es`, `fr`,
`de`, `ja`, `zh`, `ar` initially; design the enum so more languages can
be added - `user_dietary_restrictions`: list of restriction
identifiers - optional `restaurant_id` for restaurant-scoped retrieval

Response should follow a documented schema with: - `menu_metadata`:
source language, target language, image dimensions, count of parsed
dishes, warnings - `dishes`: `dish_id`, `bounding_box`, `original_text`,
`phonetic_transcription`, `translated_title`, `culinary_description`,
`flavor_profile`, `key_ingredients`, `allergen_warnings`,
`dietary_compatibility`, `price`, `evidence_status` -
`dietary_compatibility`: vegan, vegetarian, gluten-free, halal, user
conflict, and confidence/status fields where appropriate -
`processing_metadata`: stages, latency, model name/version, retrieval
status, and non-sensitive diagnostics

## Implementation

-   Use Pydantic v2 for request/response validation.
-   Use async endpoints where appropriate; avoid blocking the event loop
    with synchronous heavy inference. Use a bounded
    worker/thread/process strategy if the client library is blocking.
-   Add request IDs, stage timing, request size limits, and inference
    timeout.
-   Use a consistent error envelope and appropriate HTTP codes (400
    invalid input, 413 too large, 422 schema/input validation, 503 model
    unavailable, 504 inference timeout, 500 unexpected server error).
-   Configure CORS for explicit development origins and configurable
    production origins.
-   Support streaming/SSE only if the UI needs progressive stage
    updates. Otherwise return one validated JSON response first to
    reduce complexity.
-   Ensure model-generated output is validated before any response is
    sent.
-   Do not allow user-provided paths, SQL fragments, or arbitrary
    runtime model names.
-   Keep request/response examples in OpenAPI docs and
    `docs/api-contract.md`.

## Contract tests

Test successful response, unsupported language, empty file, invalid
image bytes, oversized upload, unavailable model, malformed VLM output,
timeout, missing optional restaurant ID, and unexpected exceptions. Test
that output bounding boxes fit image dimensions and required fields
exist.

## Acceptance criteria

-   OpenAPI schema matches actual responses.
-   Frontend can call the endpoint using a sample image.
-   All model outputs pass Pydantic validation or fail safely.
-   The API does not claim enrichment/allergen verification when those
    stages have not run.
-   Report endpoint examples, tests, and unresolved issues. Stop after
    Phase 3.
