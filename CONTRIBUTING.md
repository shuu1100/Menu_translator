# Contributing to Menu Translator

Thank you for your interest in contributing to **Menu Translator**! This project is an open-source, privacy-preserving AI culinary lens developed for the **Hacktoberfest Challenge**.

---

## 🎃 Hacktoberfest Participation Guidelines

We welcome pull requests from developers of all skill levels! To ensure high quality and safety, please review our contribution rules:

1. **Safety First**: Any modification to the `CulinarySafetyEngine` must maintain the **Zero False-Safe Mandate**: absence of an allergen statement on a printed menu can never be interpreted as proof that a dish is allergen-free.
2. **Local AI & Privacy**: All features must operate 100% locally with Ollama and SQLite. Never introduce external paid cloud inference APIs or remote telemetry without explicit maintainer approval.
3. **Automated Testing**: Every new feature or bug fix must include corresponding tests in `backend/tests/` or frontend components.
4. **No Spam PRs**: Low-effort pull requests (e.g. whitespace edits, cosmetic changes to auto-generated files) will be marked as invalid according to Hacktoberfest quality standards.

---

## 🛠️ Local Development Setup

### 1. Repository Setup
```bash
git clone https://github.com/shuu1100/Menu_translator.git
cd Menu_translator
cp .env.example .env
```

### 2. Backend Setup
```bash
# Set up Python virtual environment
python -m venv backend/.venv

# Activate environment (Windows PowerShell)
backend\.venv\Scripts\Activate.ps1
# Or on Linux/macOS: source backend/.venv/bin/activate

# Install requirements
pip install -r backend/requirements.txt

# Run test suite
$env:PYTHONPATH="."
pytest -v
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run lint
npm run build
npm run dev
```

---

## 🧪 Testing Guidelines

Before submitting a Pull Request, verify that all test suites pass cleanly:

```bash
# 1. Backend tests
$env:PYTHONPATH="."
pytest -v

# 2. Frontend linter
cd frontend
npm run lint

# 3. Frontend production build
npm run build
```

---

## 🏷️ Areas to Contribute

- **New Regional Cuisines**: Ingest verified dish records and allergen profiles into `data/culinary_knowledge.db` via `scripts/ingest_culinary_data.py`.
- **Translations & Scripts**: Improve terminology consistency for non-Latin and RTL scripts (Arabic, Japanese, Korean, Thai).
- **UI Enhancements**: Improve mobile touch interactions, high-contrast accessibility modes, or camera viewfinder overlays.
- **Evaluation Benchmarks**: Add challenging real-world menu photos to the evaluation harness in `scripts/evaluate_pipeline.py`.

---

## 📜 Code of Conduct

Please treat all contributors with respect, empathy, and constructive feedback.
