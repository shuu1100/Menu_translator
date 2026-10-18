# Security, Privacy & Data Retention Architecture

## 1. Overview & Threat Model

Menu Translator operates as a **privacy-preserving, locally hosted culinary assistant**. It is designed to run entirely on the user's infrastructure (or on local device hardware) without transmitting menu photographs, customer dietary preferences, or proprietary restaurant recipes to third-party cloud services.

This document details the security controls, boundary defenses, and data retention policies enforced across the application.

---

## 2. Input Validation & Resource Protection

### 2.1 Image Payload Hardening
- **MIME Type Whitelisting:** Accepts only `image/jpeg`, `image/png`, and `image/webp`. Payloads claiming to be images with mismatched magic bytes are rejected at the image decoding boundary (`ImageProcessor.validate_and_decode`).
- **Upload Size Limits:** Strictly constrained to $15\text{ MB}$ maximum (`max_upload_size_mb = 15`). Payloads exceeding this limit are terminated with HTTP `413 Payload Too Large` before buffer consumption.
- **Dimensional Clamping:** Input images are clamped to a maximum edge of $1024\text{ px}$ (`image_max_dimension = 1024`) maintaining exact aspect ratio, defending against pixel-flood decompression bomb attacks (ZIP/PNG bombs).
- **Safe Memory Processing:** Image decompression runs via Pillow inside memory buffers (`io.BytesIO`). No temporary files are written to the host filesystem during routine inference.

### 2.2 Bounded Concurrency & Overload Protection
- **Concurrency Semaphore:** Requests to `POST /api/v1/menus/analyze` are bounded by an `asyncio.Semaphore` (`max_concurrent_requests = 4`).
- **Overload Response:** When inference capacity is reached, excess requests are rejected with HTTP `429 Too Many Requests` or `503 Service Unavailable`, preventing VRAM/RAM exhaustion.
- **Pipeline Timeout:** End-to-end execution is governed by an overall timeout (`pipeline_timeout_seconds = 120`). Stalled or hanging model generations trigger an automatic abort and return HTTP `504 Gateway Timeout`.

---

## 3. Storage, Tenant Isolation & Prompt Injection Defense

### 3.1 Strict Cross-Restaurant Family Isolation
- **SQL Scoping:** Every database query against the SQLite culinary knowledge base filters strictly by `restaurant_id`:
  ```sql
  WHERE restaurant_id = :restaurant_id OR restaurant_id IS NULL
  ```
- **Tenant Leakage Prevention:** Scoped queries guarantee that proprietary menus, house-secret ingredients, or custom prices from one restaurant family are never retrieved by queries originating from another restaurant establishment.
- **SQL Injection Prevention:** All SQL queries use parameterized prepared statements; dynamic string concatenation is strictly prohibited. FTS5 query terms are tokenized and sanitized with `sanitize_fts5_query`.

### 3.2 Prompt Injection Neutralization
- **Untrusted OCR Text:** Native script printed on menus is treated as untrusted external user input.
- **Sanitization:** The `CulinarySafetyEngine` and `CulinaryTranslatorService` inspect extracted dish strings for prompt-injection markers (`ignore previous instructions`, `system prompt`, `override instructions`, `developer mode`, etc.) and neutralize them before passing to language models.

---

## 4. Privacy & Data Deletion Policy

### 4.1 Zero Remote Telemetry Guarantee
- **No Cloud Inference:** The application communicates exclusively with the local Ollama runtime (`http://localhost:11434`) and local SQLite database.
- **No External Analytics:** No tracking cookies, third-party CDNs, or telemetry beacons are present in the frontend PWA or backend API.

### 4.2 Ephemeral Image Processing & Deletion Policy
1. **Volatile Memory Only:** Menu photographs submitted via `POST /api/v1/menus/analyze` reside solely in volatile process memory during pipeline execution.
2. **Immediate Garbage Collection:** Image bytes and decompressed image objects are released immediately upon completion of the response payload.
3. **No Persistent Disk Storage:** Uploaded menu photos are **never** persisted to disk, uploaded to cloud storage buckets, or retained in database tables.
4. **Client-Side Storage Prohibition:** The frontend PWA does **not** persist captured menu images or dish analysis records in browser `localStorage` or `IndexedDB`. If the user closes or refreshes the page, in-memory image blobs are immediately discarded.

---

## 5. Network Security & Secrets Management

- **CORS Allowlist:** Cross-Origin Resource Sharing is restricted to permitted local origins (`http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:3001`, `http://127.0.0.1:3001`). Wildcard `*` origins are rejected in production configurations.
- **Secrets Management:** Environment variables are loaded via Pydantic `BaseSettings` reading from `.env` files. The `.env` file is excluded from git tracking via `.gitignore`.
- **Base64 Redaction:** Server-side application logs employ `Base64RedactionFilter` to automatically scrub base64 image strings from terminal output and log files.

---

## 6. Safety & Certification Boundary Notice

> [!CAUTION]
> **Not Certified for Clinical or Anaphylactic Diagnosis**:
> Menu Translator is an informational culinary translation tool. It is **NOT** a certified medical device and **MUST NOT** be used as the sole safety mechanism for life-threatening anaphylactic food allergies.
> 
> The application strictly enforces the **Zero False-Safe Mandate**: absence of an allergen statement on a printed menu is never interpreted or displayed as proof that a dish is allergen-free.
