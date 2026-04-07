# Logentum Phase 1: Hybrid Log Parser + FastAPI Backend

Production-oriented phase-1 implementation for:
- Log upload
- Hybrid parsing with Drain-style matching plus LLM fallback
- Structured JSON output
- Template cache and parser metrics
- Future-ready dashboard shell for upcoming modules

## Folder Structure

```text
Logentum/
  .env.example
  .gitignore
  backend/
    app/
      __init__.py
      config.py
      main.py
      parser/
        __init__.py
        drain_parser.py
        hybrid_parser.py
        llm_parser.py
        template_cache.py
      schemas.py
    uploads/
    requirements.txt
  frontend/
    src/
      components/
        PanelCard.jsx
        ParsedOutputPanel.jsx
        ParsingControls.jsx
        RawLogViewer.jsx
        Sidebar.jsx
        TemplateSection.jsx
        Topbar.jsx
        UploadSection.jsx
      App.jsx
      index.css
      main.jsx
    index.html
    package.json
    postcss.config.js
    tailwind.config.js
    vite.config.js
  README.md
```

## Backend (FastAPI)

### Setup

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run

```bash
uvicorn app.main:app --reload --port 8000
```

Backend API:
- `POST /upload` - Upload `.log` / `.txt`, stores in `backend/uploads`
- `POST /parse` - Uses the hybrid parser and returns parsed logs, templates, metrics, and whether the LLM was used
- `GET /templates` - Returns the current template cache and metrics
- `GET /health` - Health check

## Frontend (React + Vite + Tailwind)

### Setup

```bash
cd frontend
npm install
```

### Run

```bash
npm run dev
```

Frontend runs at `http://localhost:5173` and calls backend at `http://localhost:8000` by default.

Optional environment override:

Create `frontend/.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Notes on Extensibility

The UI is componentized and ready to extend:
- Sidebar module placeholders for Semantic Search / Anomaly Detection / Summarization / Dashboard
- Reusable cards and panel components
- Hybrid parser logic isolated in backend `app/parser/` for easy replacement of the in-memory cache with a database or vector store
- Config and secret loading centralized in backend `app/config.py`
- Clean request/response models in backend `app/schemas.py`

## Hybrid Parsing Flow

1. Drain-style parser tries to match a log line using token-length buckets and similarity scoring.
2. If confidence is high, the cached template is returned immediately.
3. If the log is unknown, similar logs are grouped into a batch.
4. The batch is sent to OpenRouter using `openai/gpt-oss-20b` with deterministic settings.
5. The extracted template is cached and registered with the Drain matcher for future reuse.

The current implementation uses an in-memory cache and parser metrics:
- `llm_calls`
- `templates_discovered`
- `cached_templates`

## Parsing Logic Implemented (Phase 1)

Current parser extracts:
- `timestamp`
- `log_level` (`INFO`, `ERROR`, `WARN`, etc.)
- `template` with placeholders (`<IP>`, `<NUM>`, `<UUID>`, `<HEX>`)
- `template_id` (short SHA-1 hash)
- `variables` captured from each line

Templates are grouped and counted for quick pattern review in the UI.

## Security Note

Do not commit API keys. Place `OPENROUTER_API_KEY` in a local `.env` file based on `.env.example`.
