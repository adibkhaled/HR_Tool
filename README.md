# HR Talent Matching Platform

Secure, tenant-scoped, human-reviewed talent matching with FastAPI, React/Vite, PostgreSQL/pgvector, deterministic local fakes, and replaceable AI providers.

Start with [docs/setup.md](docs/setup.md). API examples are in [docs/api-examples.md](docs/api-examples.md), architecture in [docs/architecture.md](docs/architecture.md), the ERD in [docs/erd.md](docs/erd.md), and the RAG flow in [docs/rag-sequence.md](docs/rag-sequence.md).

Deployment and operations guidance is in [docs/deployment.md](docs/deployment.md) and [docs/operator-runbook.md](docs/operator-runbook.md). Privacy constraints are in [docs/privacy-retention.md](docs/privacy-retention.md).

Local tests use an in-memory repository and deterministic hash embeddings. They do not claim real database, provider, cluster, staging, accessibility, or production-scale success.

## Contents

- [Features](#features)
- [Architecture](#architecture)
- [Run From GitHub](#run-from-github)
- [Run With Docker Compose](#run-with-docker-compose)
- [Run Docker Hub Images](#run-docker-hub-images)
- [Configuration](#configuration)
- [Development and testing](#development-and-testing)
- [CI/CD](#cicd)
- [Operations and security](#operations-and-security)
- [Documentation](#documentation)
- [License and copyright](#license-and-copyright)

## Product overview

The interface is a focused talent workspace with navigation for Dashboard, Resume intake, Job workspace, Candidate matching, Chat assistant, and Administration. The dashboard presents indexed employees, jobs, matches, processing status, and recent activity, while avoiding invented metrics when the API is unavailable.

## Features

- Tenant-scoped resume and job data.
- PDF, DOCX, and TXT resume intake.
- Human-reviewed candidate matching with explainable evidence.
- RAG orchestration with replaceable embedding and LLM providers.
- Deterministic local providers for development and tests.
- PostgreSQL with pgvector support.
- FastAPI health, readiness, metrics, and OpenAPI endpoints.
- React/Vite frontend served through Nginx in the containerized build.
- Correlation IDs and delivery observability.

## Architecture

```text
Browser :5147 -> Frontend (React/Vite and Nginx)
                         |
                         v
                 API (FastAPI :8000)
                    |             |
                    v             v
             PostgreSQL/pgvector  Worker
```

| Service | Purpose | Local address |
| --- | --- | --- |
| `frontend` | React application served by Nginx | `http://localhost:5147` |
| `api` | FastAPI application and OpenAPI | `http://localhost:8000` |
| `worker` | Background document-processing entrypoint | Internal service |
| `db` | PostgreSQL with pgvector | `localhost:5432` |

## Prerequisites

- Docker Desktop 4.x or newer with Docker Compose v2.
- For source development: Git, Python 3.12, `uv`, Node.js 22, and npm.

## Run From GitHub

Clone the repository and install its development dependencies:

```powershell
git clone https://github.com/adibkhaled/HR_Tool.git
Set-Location HR_Tool
Copy-Item .env.example .env
uv sync --dev
Set-Location frontend
npm ci
Set-Location ..
```

Edit `.env` and set a long, random `JWT_SECRET`. Keep provider keys and secrets out of Git.

For source development, run the API and frontend in separate terminals:

```powershell
# Terminal 1
uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2
Set-Location frontend
npm run dev
```

## Run With Docker Compose

The repository Compose file builds the application images locally from source:

```powershell
docker compose -f infra/docker/docker-compose.yml up --build
```

Open `http://localhost:5147`. Useful endpoints are:

- API health: `http://localhost:8000/health`
- API readiness: `http://localhost:8000/ready`
- OpenAPI UI: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`
- Metrics: `http://localhost:8000/metrics`

Run in the background or stop the stack:

```powershell
docker compose -f infra/docker/docker-compose.yml up --build -d
docker compose -f infra/docker/docker-compose.yml logs -f api
docker compose -f infra/docker/docker-compose.yml down
```

## Run Docker Hub Images

After successful CI, the publishing workflow creates:

```text
YOUR_DOCKERHUB_USERNAME/hr-tool-api
YOUR_DOCKERHUB_USERNAME/hr-tool-frontend
```

The backend image is reused by both `api` and `worker`. PostgreSQL remains the public `pgvector/pgvector:pg16` image.

Pull the images on a machine with Docker Desktop:

```powershell
docker login
docker pull YOUR_DOCKERHUB_USERNAME/hr-tool-api:latest
docker pull YOUR_DOCKERHUB_USERNAME/hr-tool-frontend:latest
```

For deployment, use a Compose file with these image entries while retaining the environment, health checks, dependencies, and ports from `infra/docker/docker-compose.yml`:

```yaml
services:
	api:
		image: YOUR_DOCKERHUB_USERNAME/hr-tool-api:latest
	worker:
		image: YOUR_DOCKERHUB_USERNAME/hr-tool-api:latest
	frontend:
		image: YOUR_DOCKERHUB_USERNAME/hr-tool-frontend:latest
```

Use `sha-<commit>` tags for reproducible deployments instead of `latest`.

## Configuration

Copy `.env.example` to `.env`. Important variables include:

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | Runtime environment |
| `POSTGRES_PASSWORD` | PostgreSQL password used by Compose |
| `DATABASE_URL` | Database URL for local non-Compose development |
| `PGVECTOR_ENABLED` | Enables vector-store integration |
| `JWT_SECRET` | Authentication secret; use 32+ random characters outside development |
| `OBJECT_STORAGE_ENDPOINT` | Object-storage endpoint |
| `OBJECT_STORAGE_BUCKET` | Source-document bucket |
| `EMBEDDING_MODEL` | Embedding model identifier |
| `LLM_PROVIDER` | LLM provider name |
| `LLM_API_KEY` | Provider credential; never commit it |
| `LLM_MODEL` | LLM model identifier |
| `LLM_BASE_URL` | LLM API base URL |
| `CORS_ORIGINS` | JSON list of browser origins |

## Development and testing

```powershell
uv run ruff check backend tests
uv run mypy backend
uv run pytest
Set-Location frontend
npm run lint
npm run typecheck
npm run test
npm run build
Set-Location ..
```

## CI/CD

The CI workflow runs on pull requests and pushes to `master` or `main`. It performs backend linting, frontend linting, type checking, frontend tests and build, and a Trivy security scan. The backend pytest step is currently disabled because the CI environment needs required `.env` configuration; run it locally with `uv run pytest` after creating `.env`.

After CI succeeds, `docker-publish.yml` builds and publishes both images to Docker Hub. Configure these GitHub repository secrets:

```text
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
```

Use a Docker Hub personal access token with push permission. Never place the token in source code or workflow files.

## Operations and security

- Define retention and deletion rules for documents, chunks, embeddings, matches, chat history, and audit records.
- Logs must not contain document text, tokens, passwords, or provider payloads.
- Use managed PostgreSQL/pgvector with backups, encryption, network controls, and tested restores in production.
- This platform supports human-reviewed matching and does not automate hiring decisions.

## Documentation

- [Setup guide](docs/setup.md)
- [API examples](docs/api-examples.md)
- [Architecture](docs/architecture.md)
- [Deployment guide](docs/deployment.md)
- [Operations guide](docs/operations.md)
- [Operator runbook](docs/operator-runbook.md)
- [Privacy and retention](docs/privacy-retention.md)
- [RAG sequence](docs/rag-sequence.md)
- [Entity relationship diagram](docs/erd.md)

## License and copyright

Copyright (c) 2026 Adibqa Solution. All rights reserved.

This repository is provided for authorized use by Adibqa Solution and its permitted users. No license is granted to copy, modify, distribute, or use this software outside terms separately agreed with the copyright holder.
