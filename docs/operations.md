# Operations

## Local stack

Copy `.env.example`, set `POSTGRES_PASSWORD` and a 32+ character `JWT_SECRET`, then run `docker compose -f infra/docker/docker-compose.yml up --build`. The API is available at `http://localhost:8000`; OpenAPI is at `/docs` and the frontend is at `http://localhost:8080`.

## Health and metrics

`/health` confirms the process is alive. `/ready` checks configured dependencies and returns `503` until the database and pgvector settings are ready. `/metrics` exposes request, processing, matching, and dependency counters in Prometheus text format.

Every request returns `X-Correlation-ID`; pass the same value to worker and audit records. Logs must not contain source document text, tokens, passwords, or provider payloads.

## Privacy and retention

Retention duration, jurisdiction, object-storage lifecycle, and deletion approval are deployment configuration gates. Before production, configure them with the data-protection owner and verify source files, chunks, embeddings, match snapshots, chat history, and audit lineage are reconciled. This platform does not automate hiring decisions.

## Rollback

Disable new matching at the ingress or feature-flag layer while leaving completed match snapshots and audit history readable. Roll back API and worker images independently, then reconcile queued operations before re-enabling matching.
