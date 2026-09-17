# HR Talent Matching Platform

Secure, tenant-scoped, human-reviewed talent matching with FastAPI, React/Vite, PostgreSQL/pgvector, deterministic local fakes, and replaceable AI providers.

Start with [docs/setup.md](docs/setup.md). API examples are in [docs/api-examples.md](docs/api-examples.md), architecture in [docs/architecture.md](docs/architecture.md), the ERD in [docs/erd.md](docs/erd.md), and the RAG flow in [docs/rag-sequence.md](docs/rag-sequence.md).

Deployment and operations guidance is in [docs/deployment.md](docs/deployment.md) and [docs/operator-runbook.md](docs/operator-runbook.md). Privacy constraints are in [docs/privacy-retention.md](docs/privacy-retention.md).

Local tests use an in-memory repository and deterministic hash embeddings. They do not claim real database, provider, cluster, staging, accessibility, or production-scale success.
