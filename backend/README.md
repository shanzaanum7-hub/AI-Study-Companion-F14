# AI Study Companion — Backend

A production-ready **FastAPI** backend for an AI-powered study companion.
Upload PDF documents, index them into a Qdrant vector database, and query
them with semantic search and RAG-powered Q&A, study plans, summaries, and
flashcards.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 / Python 3.12 |
| Validation | Pydantic v2 + pydantic-settings |
| PDF extraction | pypdf |
| Tokenisation | tiktoken |
| Embeddings | sentence-transformers |
| Vector DB | Qdrant |
| LLM providers | OpenAI · Anthropic · Ollama |
| Server | Uvicorn |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py               # FastAPI app factory, middleware, routers
│   ├── config.py             # Pydantic Settings (loads from .env)
│   │
│   ├── routers/
│   │   ├── health.py         # GET  /api/v1/health  (liveness + readiness)
│   │   ├── upload.py         # POST /api/v1/upload
│   │   ├── retrieval.py      # POST /api/v1/retrieval/search|ask
│   │   └── study_plan.py     # POST /api/v1/study-plan/generate|summary|flashcards
│   │
│   ├── services/
│   │   ├── pdf_service.py        # PDF text extraction (pypdf)
│   │   ├── chunk_service.py      # Token-window chunking
│   │   ├── embedding_service.py  # Dense vector generation
│   │   ├── qdrant_service.py     # Qdrant CRUD + search
│   │   ├── retrieval_service.py  # Embed → search → map results
│   │   └── llm_service.py        # OpenAI / Anthropic / Ollama facade
│   │
│   ├── models/
│   │   ├── schemas.py            # Request payload schemas
│   │   └── response_models.py    # Typed response envelopes
│   │
│   ├── utils/
│   │   ├── file_handler.py       # Upload validation & persistence helpers
│   │   └── tokenizer.py          # Token counting & splitting utilities
│   │
│   └── uploads/                  # Runtime file storage (git-ignored)
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start

### 1. Clone & enter the directory

```bash
git clone <repo-url>
cd AI-Study-Companion-F14/backend
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in your API keys and settings
```

### 5. Start Qdrant (Docker)

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 6. Run the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or via the `__main__` entry point (uses settings from `.env`):

```bash
python -m app.main
```

---

## API Reference

Interactive docs are available at **http://localhost:8000/docs** (Swagger UI)
and **http://localhost:8000/redoc** when `ENVIRONMENT` is not `production`.

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | App name, version, uptime |
| `GET` | `/api/v1/health/live` | Liveness probe |
| `GET` | `/api/v1/health/ready` | Readiness probe (checks Qdrant + LLM) |

### Upload

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/upload` | Upload a PDF document |
| `GET` | `/api/v1/upload` | List all documents |
| `GET` | `/api/v1/upload/{document_id}` | Get document status |
| `DELETE` | `/api/v1/upload/{document_id}` | Delete a document |

### Retrieval

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/retrieval/search` | Semantic similarity search |
| `POST` | `/api/v1/retrieval/ask` | RAG question answering |

### Study Plan

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/study-plan/generate` | Generate a study plan |
| `POST` | `/api/v1/study-plan/summary` | Summarise documents or a topic |
| `POST` | `/api/v1/study-plan/flashcards` | Generate flashcards |

---

## Configuration

All settings are controlled via environment variables (or `.env`).
See `.env.example` for the full list with descriptions.

Key settings:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai` · `anthropic` · `ollama` |
| `OPENAI_API_KEY` | — | Required when `LLM_PROVIDER=openai` |
| `QDRANT_HOST` | `localhost` | Qdrant server host |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | HuggingFace model for embeddings |
| `CHUNK_SIZE` | `512` | Tokens per chunk |
| `RETRIEVAL_TOP_K` | `5` | Results returned per search |
| `DEBUG` | `false` | Enables reload, verbose errors, API docs |

---

## LLM Providers

Switch providers by setting `LLM_PROVIDER` in your `.env`:

```
# OpenAI (default)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Ollama (local — no API key needed)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

---

## Development Notes

- **Business logic** is stubbed with `# TODO` comments in every service and router.
  The architecture and interfaces are production-ready; fill in the TODOs to activate
  each feature.
- **Uploads directory** (`app/uploads/`) is excluded from git via `.gitkeep`.
- **API docs** are disabled automatically when `ENVIRONMENT=production`.
- **CORS** origins are configured in `ALLOWED_ORIGINS`. Update this list before deploying.
