# System Architecture

The HR Talent Matching Platform is a clean-architecture monorepo.

- `backend/app/api`: HTTP routes, middleware, and request boundaries.
- `backend/app/services`: application and domain orchestration.
- `backend/app/repositories`: persistence and external storage adapters.
- `backend/app/models`: SQLAlchemy persistence models.
- `backend/app/schemas`: typed API contracts.
- `backend/app/core`: configuration, logging, and cross-cutting runtime concerns.
- `backend/app/rag`, `backend/app/ai`, `backend/app/chat`: replaceable AI and conversational workflows.
- `frontend/src`: React UI, server-state clients, local state, and user-facing workflows.
- `infra/docker`, `infra/kubernetes`: deployment definitions.
- `tests/backend`, `tests/frontend`: backend and frontend verification suites.

`/health` reports process liveness only. `/ready` reports whether configured runtime dependencies are ready and returns HTTP 503 when they are not. Every response receives an `X-Correlation-ID` for request tracing.

See [the ERD](erd.md), [the RAG sequence](rag-sequence.md), [deployment guidance](deployment.md), and [the operator runbook](operator-runbook.md) for runtime relationships and procedures.
