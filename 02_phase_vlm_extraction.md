# Phase 2 Prompt --- Local Vision-Language Model and Menu Extraction

Implement the visual inference service only after Phase 1 passes.

## Goal

Accept a menu image and extract structured dish candidates with original
text, optional phonetic transcription, prices, ingredient/subtitle text,
reading order, and normalized bounding boxes. The VLM must understand
multi-column and irregular layouts rather than returning a single
unstructured OCR paragraph.

## Model plan

Create a provider interface such as `MenuVisionProvider` with methods
for health checking and image extraction. Implement an Ollama provider
first, configured by environment variables. Benchmark: - Preferred
candidate: `qwen3-vl:8b` where supported and feasible. - Smaller
candidate: `qwen3-vl:4b` or `qwen2.5vl:3b`. - Document baseline:
`qwen2.5vl:7b`. Model tags and availability can change; validate the
exact tag against the installed runtime. Keep model selection
configurable. Provide a Hugging Face Transformers/vLLM adapter only if
the project needs it; do not maintain two inference paths before the
first path works.

## Image preprocessing

-   Validate MIME type from file bytes, decode safely, reject malformed
    images, and enforce file-size and pixel-count limits.
-   Correct EXIF orientation.
-   Keep the original image for final overlays.
-   Provide optional OpenCV preprocessing: resize while preserving
    aspect ratio, contrast-limited adaptive histogram equalization
    (CLAHE), denoising only if needed, and perspective correction only
    when reliably estimated.
-   Never destructively stretch a long menu into a square. Preserve
    aspect ratio and allow tiled/cropped inference for very long menus
    if evaluation shows the model misses small text.
-   Record the transformations so coordinates can be mapped back to the
    original image.

## Extraction prompt behavior

Instruct the model to: 1. Read every visible menu item in natural
reading order, including columns. 2. Preserve the native script and
punctuation exactly when legible. 3. Separate dish title,
subtitle/ingredients, section/category, price, and other text. 4. Return
a bounding box around the dish's relevant text block, not an arbitrary
point. 5. Return coordinates normalized to 0--1000 (`xmin`, `ymin`,
`xmax`, `ymax`) or use one documented pixel convention consistently.
Normalize to the original image dimensions before sending to the
frontend. 6. Never guess unreadable text; use empty text plus an
uncertainty marker. 7. Do not infer allergens or recipe ingredients from
the image unless explicitly printed. That happens in later enrichment
phases. 8. Return JSON only, matching a Pydantic schema.

## Backend types

Create Pydantic models for: - `MenuExtractionResult` - `MenuTextBlock` -
`BoundingBox` - `ExtractionWarning` Include stable IDs, source text,
source language if confidently identified, reading order, price as
display text (do not assume currency), confidence if the runtime
supports a meaningful confidence estimate, and extraction notes.

## Reliability

-   Parse model output defensively. Handle fenced JSON, truncated
    output, unexpected keys, missing required fields, invalid
    coordinates, and empty results.
-   Never execute model-produced code.
-   Retry at most once for recoverable malformed JSON with a repair
    prompt that includes the schema, not secrets.
-   If output remains invalid, return a clear error and preserve
    diagnostics without exposing raw image data.
-   Set a timeout and handle model-unavailable errors gracefully.
-   Keep model output and runtime logs separate from user-visible
    content.

## Tests and evaluation

Create fixtures for clear menus, low-light photos, skewed images,
multi-column menus, small fonts, mixed scripts, and menus with
decorative graphics. Include synthetic fixtures if licensed data is
unavailable. Metrics: character error rate (CER), word error rate (WER),
dish-level exact match, price-to-dish association accuracy,
reading-order accuracy, bounding-box IoU, JSON validity rate, latency,
and peak memory. Report metrics by language and image condition when
possible.

## Acceptance criteria

-   A sample image yields structured blocks with valid coordinates.
-   Coordinates visibly line up with the original image.
-   Tests cover malformed images and malformed model output.
-   No ingredient/allergen claims are generated in the extraction stage.
-   Include model download/run instructions and a benchmark script. Stop
    after Phase 2.
