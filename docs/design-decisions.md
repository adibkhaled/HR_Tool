# Design decisions

- Keep the first deployment modular: FastAPI, a worker, PostgreSQL/pgvector, and a React client share explicit domain contracts.
- Keep external AI and vector dependencies behind interfaces so tests use deterministic fakes and production providers can be configured independently.
- Treat readiness, evidence, model/policy versions, audit records, and human review as first-class state.
- Use tenant and lifecycle filters before retrieval; never use protected attributes as ranking inputs.
- Keep long work asynchronous and idempotent. A normal interactive request targets five seconds under the documented operating budget, but local tests do not prove production latency.
- Use correlation IDs across requests, operations, worker work, and audit entries for incident investigation.
