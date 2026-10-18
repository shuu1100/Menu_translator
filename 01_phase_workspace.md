# Phase 1 Prompt --- Workspace Audit and Project Skeleton

You are a senior full-stack AI engineer. Implement Phase 1 only for the
Menu Translator project. First inspect the entire existing repository
and report the current structure, runtime versions, working features,
and risks. Do not overwrite working files or fabricate completed work.

## Stack

-   Frontend: Next.js + React + TypeScript, Tailwind CSS, Lucide icons,
    installable PWA foundations.
-   Backend: Python 3.11+ (or compatible installed version), FastAPI,
    Pydantic v2, Uvicorn.
-   Image handling: Pillow and OpenCV.
-   Local database: SQLite; later phases add FTS5 and sqlite-vec.
-   Tests: pytest for backend; frontend's existing test framework or
    Vitest/Testing Library if none exists.
-   Local model runtime: configurable Ollama URL/model name. Do not
    require a hosted API key.

## Tasks

1.  Audit repository, git status, active branch, package manager, Python
    environment, existing tests, and README. Preserve uncommitted user
    work.
2.  Create a maintainable monorepo layout, adapting rather than forcing
    this exact structure:
    -   `frontend/` Next.js app
    -   `backend/app/main.py`
    -   `backend/app/api/`
    -   `backend/app/schemas/`
    -   `backend/app/services/`
    -   `backend/app/db/`
    -   `backend/tests/`
    -   `data/` for documented sample data only
    -   `docs/`
3.  Add dependency manifests and lockfiles consistent with the
    repository's current package managers.
4.  Add `.env.example` for `OLLAMA_BASE_URL`, `VISION_MODEL`,
    `DATABASE_PATH`, upload limits, CORS origins, log level, and
    inference timeout. No real secrets.
5.  Add `.gitignore` entries for virtual environments, `.next`, build
    artifacts, `.env`, model weights, private restaurant recipes,
    uploaded photos, caches, and generated training datasets.
6.  Add `/health` and `/api/v1/health` endpoints with explicit service
    status. Health must not falsely report that model inference works if
    the model is unavailable.
7.  Add structured logging and central exception handling; never log
    image base64 payloads.
8.  Add README setup instructions for Windows and Linux/WSL,
    frontend/backend development commands, local model installation,
    tests, and troubleshooting.
9.  Add a simple CI workflow if the repository uses GitHub Actions:
    install dependencies, lint/type-check frontend, run backend tests.
    Do not require GPU in CI.

## Acceptance criteria

-   Fresh install steps are reproducible.
-   Frontend starts and backend starts independently.
-   Health endpoint returns valid JSON.
-   Tests run without a GPU or model download.
-   `.env` and user data are ignored by Git.
-   Provide a concise audit report, files changed, commands run, test
    results, and remaining blockers. Stop after Phase 1.
