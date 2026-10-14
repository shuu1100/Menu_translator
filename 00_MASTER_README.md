# Menu Translator --- Hacktoberfest Open-Source AI Challenge

## Purpose

Build a privacy-preserving, locally deployable restaurant menu
translator. It accepts a menu photo, extracts dish text and bounding
boxes, enriches dish records using local restaurant knowledge,
translates meaning rather than only words, highlights possible allergens
and dietary conflicts, and renders interactive overlays in a Progressive
Web App.

## Source-of-truth design

This plan follows the uploaded `Menu Translator Development Plan.md`:
React/Next.js PWA, Tailwind CSS and Lucide, Python FastAPI, Pydantic v2,
OpenCV/Canvas preprocessing, a vision-language model (VLM), SQLite +
FTS5 + sqlite-vec hybrid RAG, Reciprocal Rank Fusion, optional
LoRA/QLoRA fine-tuning with Unsloth, and local inference through Ollama
or a compatible Hugging Face/vLLM/llama.cpp deployment.

## Recommended phases

1.  Workspace audit and project skeleton
2.  VLM inference and visual menu extraction
3.  Backend contracts, validation, and pipeline orchestration
4.  SQLite culinary knowledge base and hybrid RAG
5.  Translation, cultural context, dietary/allergen safety
6.  Dataset creation, evaluation, and optional fine-tuning
7.  Next.js PWA, camera capture, image overlays, and UX
8.  Integration, offline mode, security, and performance
9.  Final QA, demo, documentation, and Hacktoberfest release

Give each phase prompt to Antigravity separately, in order. Do not start
later phases until the current phase's acceptance criteria pass. Inspect
the repository before editing, preserve existing working code, and make
small, testable changes.

## Model recommendation

-   **Primary local baseline to benchmark:** `qwen3-vl:8b` in Ollama if
    supported by the machine and current Ollama version.
-   **Smaller local fallback:** `qwen3-vl:4b` or `qwen2.5vl:3b`.
-   **Document's reference baseline:** `qwen2.5vl:7b`.
-   **Higher-accuracy benchmark candidate:** a larger Qwen3-VL variant
    on a capable GPU.
-   Keep a model adapter interface so model choice is configuration, not
    hard-coded application logic.
-   Do not assume the newest/largest model is best. Run the same
    held-out menu evaluation set and compare text accuracy, bounding-box
    quality, JSON validity, latency, memory, and multilingual
    performance before selecting the default.

## Critical safety rule

Never present an inferred allergen absence as proof that a dish is safe.
Use known restaurant recipe records as the authoritative source when
available. Distinguish `confirmed`, `possible`, and `unknown`; show
uncertainty and advise diners with severe allergies to confirm with
restaurant staff. A model-generated ingredient list is not a verified
recipe.

## Global engineering rules for every phase

-   Type hints, clear modules, useful logging, and actionable errors.
-   No hard-coded API keys or secrets. Prefer local inference; if an
    optional external provider is added, make it opt-in and document
    data flow.
-   Never log base64 images or sensitive recipe details by default.
-   Use environment variables for runtime configuration, with
    `.env.example` containing placeholders only.
-   Add unit tests for business logic and integration tests for
    boundaries.
-   Do not invent ingredient/allergen facts; cite the local record or
    mark unknown.
-   Use deterministic, low-temperature inference for extraction;
    validate and repair outputs safely without trusting generated JSON.
-   Do not claim offline AI inference unless the model weights and
    runtime are installed locally. The PWA shell may work offline even
    when model inference is unavailable.
