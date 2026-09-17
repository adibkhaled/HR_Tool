# Local setup

## Prerequisites

- Python 3.12 and `uv`
- Node.js 22 and npm
- Docker Desktop for the Compose smoke test

Install dependencies:

```powershell
uv sync --dev
Set-Location frontend
npm ci
Set-Location ..
```

Copy `.env.example` to `.env` and replace development-only secrets. The in-memory repository and deterministic hash embeddings are suitable for tests only. Real PostgreSQL/pgvector, object storage, embedding models, and LLM providers require separately configured services and credentials.

Run the local checks:

```powershell
uv run pytest -q
Set-Location frontend
npm run lint
npm run typecheck
npm test -- --run
npm run build
Set-Location ..
```

Start the API with `uv run uvicorn backend.app.main:app --reload` and the frontend with `npm run dev` from `frontend`. The API is available at `http://localhost:8000`; OpenAPI is at `/docs` and `/openapi.json`.
