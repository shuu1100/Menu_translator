# Menu Translator — Local AI Culinary Lens

A privacy-preserving, locally deployable restaurant menu translator and dietary allergen scanner for the **Hacktoberfest Open-Source AI Challenge**.

---

## Architecture & Features

- **Frontend**: Next.js App Router, React 19, TypeScript, Tailwind CSS, Lucide icons, installable PWA foundations.
- **Backend**: Python FastAPI, Pydantic v2, Pillow & OpenCV-headless, structured logging with base64 payload redaction.
- **Local AI Engine**: Powered by Ollama running Vision-Language Models (default: `qwen3-vl:8b`, with fallbacks to `qwen3-vl:4b` or `qwen2.5vl:7b`).
- **Allergen & Safety Guarantee**: Strict safety policy distinguishing `confirmed`, `possible`, and `unknown` allergens. Inferred allergen absence is never presented as safety proof.

---

## Prerequisites

- **Python**: 3.11+ (Tested and verified with 3.14+)
- **Node.js**: 20+ (Tested with v24 LTS) & npm 10+
- **Ollama**: Installed and running locally ([ollama.com](https://ollama.com))

---

## Quickstart Guide

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone https://github.com/your-org/Hack_to_october.git
cd Hack_to_october

# Copy environment variables
cp .env.example .env
```

### 2. Download Local Vision Model (Ollama)

Ensure Ollama is running, then pull the recommended vision model:

```bash
ollama pull qwen3-vl:8b
```

*(For low-VRAM machines, you can also use `ollama pull qwen2.5vl:3b` or `ollama pull qwen3-vl:4b` and update `VISION_MODEL` in `.env`)*.

---

### 3. Backend Setup

#### Windows (PowerShell)
```powershell
# Create and activate virtual environment
python -m venv backend/.venv
backend\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# Run the backend server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Linux / macOS / WSL
```bash
# Create and activate virtual environment
python3 -m venv backend/.venv
source backend/.venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run the backend server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend will be running at:
- **API Base**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **Health Diagnostics**: `http://127.0.0.1:8000/health` or `http://127.0.0.1:8000/api/v1/health`
- **Visual Menu Extraction**: `POST http://127.0.0.1:8000/api/v1/extract` (multipart/form-data with `file` and optional `apply_clahe=true`)

---

### 4. Running VLM Benchmarks (Phase 2)

A benchmark suite is provided to test the local VLM (`qwen3-vl:8b`) on synthetic multi-column restaurant menus under clear, low-light, noisy, and decorative conditions:

```bash
# Run benchmark on clear condition
python scripts/benchmark_vlm.py clear

# Run benchmark across all visual conditions
python scripts/benchmark_vlm.py clear low_light noisy decorative
```

The benchmark reports **Dish Match Rate**, **Character Error Rate (CER)**, **Word Error Rate (WER)**, **Bounding-Box IoU**, and **Inference Latency**.

---

### 4. Frontend Setup

In a separate terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser. The frontend will automatically query `http://127.0.0.1:8000/health` to display live status of the API, Database, and local Ollama VLM model.

---

## Running Tests

All unit and integration tests run entirely locally **without requiring a GPU or model download**:

```bash
# Activate backend virtual environment
backend/.venv/Scripts/Activate.ps1   # Windows
# source backend/.venv/bin/activate  # Linux/WSL

# Run backend pytest suite
pytest -v backend/tests
```

Frontend production build and type checking:
```bash
cd frontend
npm run build
```

---

## Project Structure

```text
Hack_to_october/
├── .github/workflows/ci.yml       # CI workflow for linting, build, and tests
├── backend/
│   ├── app/
│   │   ├── api/v1/health.py       # Detailed health diagnostic router
│   │   ├── core/                  # Config, base64-safe logging, custom exceptions
│   │   ├── db/                    # Database connection & path management
│   │   ├── schemas/health.py      # Pydantic schemas for health and system status
│   │   ├── services/              # Business logic & Ollama health inspector
│   │   └── main.py                # FastAPI factory & lifespan
│   ├── tests/                     # Pytest suite (mocked offline & live checks)
│   ├── pyproject.toml             # Python package & pytest configuration
│   └── requirements.txt           # Python dependency manifest
├── data/
│   ├── sample_menus/              # Documented CC0 sample menus & ground truth
│   ├── uploads/                   # Upload scratch area (.gitignore)
│   ├── recipes/private/           # Private recipe storage (.gitignore)
│   └── cache/                     # Query & model cache (.gitignore)
├── docs/
│   └── architecture.md            # Architecture diagram & data flow
├── frontend/
│   ├── src/app/
│   │   ├── layout.tsx             # Root layout with PWA metadata
│   │   ├── manifest.ts            # Next.js PWA Web App Manifest
│   │   └── page.tsx               # Phase 1 Live status dashboard (Lucide icons)
│   └── package.json               # Next.js, React, Tailwind, Lucide dependencies
├── .env.example                   # Safe environment template
├── .gitignore                     # Git ignore rules for envs, models, caches, data
├── 00_MASTER_README.md            # 9-phase master Hacktoberfest specification
└── README.md                      # Developer onboarding & setup guide
```

---

## Troubleshooting

- **Ollama reports "unavailable" on `/health`**:
  Make sure Ollama is running (`ollama serve` or check your task manager).
- **Health status is "degraded" (Model missing)**:
  Run `ollama pull qwen3-vl:8b` (or match the name in `.env`). The API accurately reflects whether the model is downloaded and ready, preventing false claims.
- **Port conflicts**:
  Change `PORT` in `.env` or run uvicorn with `--port <NEW_PORT>`.
