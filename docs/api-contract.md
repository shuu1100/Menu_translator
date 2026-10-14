# Menu Translator API Contracts (v1)

This specification documents the primary API contracts for the Menu Translator backend service.

---

## 1. Health Diagnostics

### `GET /health` and `GET /api/v1/health`

Evaluates system health and distinguishes between backend availability, Ollama reachability, installed model presence, and active inference availability.

- **Query Parameters**:
  - `check_inference` (bool, optional, default: `false`): If true, executes an active lightweight probe to confirm model inference readiness.

#### Response Example (200 OK)
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-10-15T03:41:42.249Z",
  "services": {
    "api": {
      "status": "ok",
      "message": "FastAPI service is running",
      "details": {
        "environment": "development",
        "version": "0.1.0"
      }
    },
    "database": {
      "status": "ok",
      "message": "Database directory accessible",
      "details": {
        "path": "data/culinary_knowledge.db",
        "exists": false,
        "writable": true
      }
    },
    "model_service": {
      "status": "ok",
      "message": "Model 'qwen3-vl:8b' is installed and available in Ollama.",
      "details": {
        "provider": "ollama",
        "base_url": "http://localhost:11434",
        "configured_model": "qwen3-vl:8b",
        "available_models": ["qwen3-vl:8b"],
        "backend_available": true,
        "ollama_server_available": true,
        "model_installed": true,
        "active_inference_checked": false,
        "active_inference_available": null,
        "latency_ms": 42.1,
        "inference_ready": true
      }
    }
  }
}
```

---

## 2. Configuration & Reference Metadata

### `GET /api/v1/config/languages`

Returns the list of supported target languages for translation.

#### Response Example (200 OK)
```json
[
  {"code": "en", "name": "English"},
  {"code": "es", "name": "Spanish (Español)"},
  {"code": "fr", "name": "French (Français)"},
  {"code": "de", "name": "German (Deutsch)"},
  {"code": "ja", "name": "Japanese (日本語)"},
  {"code": "zh", "name": "Chinese (中文)"},
  {"code": "ar", "name": "Arabic (العربية)"},
  {"code": "it", "name": "Italian (Italiano)"},
  {"code": "pt", "name": "Portuguese (Português)"},
  {"code": "ko", "name": "Korean (한국어)"}
]
```

---

## 3. End-to-End Menu Analysis Pipeline

### `POST /api/v1/menus/analyze`

Executes the complete pipeline: image validation $\to$ aspect-ratio preserving preprocessing $\to$ local VLM visual extraction $\to$ culinary enrichment hook $\to$ dietary conflict cross-checking.

- **Content-Type**: `multipart/form-data`
- **Request Parameters**:
  - `file` (File, required): Menu photo (`image/jpeg`, `image/png`, `image/webp`).
  - `target_language` (string, optional, default: `"en"`): Target language code (`en`, `es`, `fr`, etc.).
  - `user_dietary_restrictions` (string, optional): Comma-separated or JSON array of dietary restrictions (e.g. `"gluten-free, vegan"`).
  - `restaurant_id` (string, optional): Scoped restaurant ID for knowledge base lookup.
  - `apply_clahe` (bool, optional, default: `false`): Enables CLAHE contrast enhancement for low-light photos.

#### Response Example (200 OK)
```json
{
  "menu_metadata": {
    "source_language": "it",
    "target_language": "en",
    "image_width": 1200,
    "image_height": 1600,
    "dish_count": 2,
    "restaurant_id": null,
    "warnings": []
  },
  "dishes": [
    {
      "dish_id": "d1a8c9e2",
      "reading_order": 1,
      "section": "Primi Piatti",
      "bounding_box": {
        "xmin": 0.08,
        "ymin": 0.15,
        "xmax": 0.48,
        "ymax": 0.25,
        "pixel_x": 96,
        "pixel_y": 240,
        "pixel_width": 480,
        "pixel_height": 160
      },
      "original_text": "Tagliatelle al Ragù",
      "phonetic_transcription": null,
      "translated_title": "Tagliatelle al Ragù (Target: en)",
      "culinary_description": "Fresh handmade egg ribbons with slow-braised bolognese meat sauce",
      "flavor_profile": null,
      "key_ingredients": ["Fresh handmade egg ribbons with slow-braised bolognese meat sauce"],
      "allergen_warnings": [
        {
          "allergen": "gluten",
          "status": "possible",
          "source": "printed_menu_text",
          "notes": "Keyword match from printed description"
        },
        {
          "allergen": "eggs",
          "status": "possible",
          "source": "printed_menu_text",
          "notes": "Keyword match from printed description"
        }
      ],
      "dietary_compatibility": {
        "vegan": "no",
        "vegetarian": "no",
        "gluten_free": "no",
        "halal": "unknown",
        "user_conflicts": ["Non-vegan ingredients detected", "Meat or seafood detected"],
        "confidence_notes": "Phase 3 stubbed baseline; unverified against restaurant recipe database."
      },
      "price": "€16.50",
      "currency": "€",
      "evidence_status": "unverified"
    }
  ],
  "processing_metadata": {
    "request_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "total_latency_ms": 2840.5,
    "model_name": "qwen3-vl:8b",
    "retrieval_status": "stubbed_not_run_in_phase_3",
    "stages": [
      {"stage": "preprocessing", "duration_ms": 42.1},
      {"stage": "visual_extraction", "duration_ms": 2780.2},
      {"stage": "culinary_enrichment_stub", "duration_ms": 3.2},
      {"stage": "dietary_evaluation", "duration_ms": 1.1}
    ],
    "diagnostics": {
      "applied_clahe": false,
      "user_restrictions_evaluated": ["vegan", "vegetarian"]
    }
  },
  "safety_disclaimer": "CRITICAL SAFETY NOTICE: Allergen and dietary data at this stage are unverified. Never rely solely on AI for life-threatening allergies. Confirm all ingredients with restaurant staff."
}
```

---

## 4. Error Status Codes

| HTTP Status | Error Code | Description |
| :--- | :--- | :--- |
| **400 Bad Request** | `INVALID_IMAGE` | Corrupted image or unsupported MIME type |
| **413 Payload Too Large** | `PAYLOAD_TOO_LARGE` | Uploaded image exceeds max upload size (15MB) |
| **422 Unprocessable** | `UNSUPPORTED_LANGUAGE` | Provided target language is not supported |
| **503 Service Unavailable** | `MODEL_SERVICE_UNAVAILABLE` | Local Ollama daemon is offline or unreachable |
| **504 Gateway Timeout** | `INFERENCE_TIMEOUT` | Model inference exceeded configured timeout (300s) |
| **500 Server Error** | `PIPELINE_ERROR` | Unexpected backend pipeline error |
