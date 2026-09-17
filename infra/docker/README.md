# Docker deployment

Compose starts the API, worker, frontend, and pgvector database. Run `infra/docker/smoke.ps1` with Docker Desktop to build the stack and verify the API health endpoint. The smoke test is local-only and does not validate external providers or production data services.
