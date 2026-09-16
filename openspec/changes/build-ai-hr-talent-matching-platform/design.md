## Context

The repository is a greenfield OpenSpec project with no application code or existing infrastructure. The approved HR plan fixes the initial technology baseline: React with TypeScript and Vite, Material UI, TanStack Query, Zustand, FastAPI, SQLAlchemy, PostgreSQL with pgvector, LangChain, Sentence Transformers, JWT authentication, Docker Compose, GitHub Actions, and Prometheus/Grafana. See proposal.md for motivation and spec.md for the behavioral contract.

The platform handles sensitive employee data and model-generated employment recommendations. The design therefore separates user-facing request handling from durable work, preserves source evidence and model versions, and requires human review. Retention duration and jurisdiction-specific policy are configuration and deployment gates rather than hard-coded business rules.

## Goals / Non-Goals

**Goals:**

- Deliver a clean-architecture monorepo with a React frontend, modular async FastAPI backend, PostgreSQL/pgvector persistence, and replaceable AI/vector providers.
- Support PDF, DOCX, and TXT resume/job ingestion, chat-assisted job authoring, repository management, matching, candidate explanations, and conversational search.
- Provide JWT authentication and HR Admin, Recruiter, and Viewer authorization with audit logging.
- Keep normal chat and match requests under five seconds when indexed data and provider latency are within the agreed budget; use durable asynchronous operations for longer work.
- Support 10,000+ resumes through indexed metadata filters, pgvector similarity search, pagination, bounded workers, and load-tested APIs.
- Produce OpenAPI documentation, ERD/schema documentation, request/response examples, automated tests, local Docker deployment, CI/CD, and observability dashboards.

**Non-Goals:**

- Automated hiring decisions, rejection, offer generation, or unsupervised employment action.
- Inferring protected characteristics or using them as ranking features.
- Candidate communication, interview scheduling, payroll, or a full HRIS replacement.
- Replacing pgvector in the first deployment; the vector repository is abstracted so Qdrant or another provider can be introduced later.

## Decisions

### 1. Clean-architecture monorepo with modular FastAPI backend

Use `backend/app` modules for `api`, `services`, `repositories`, `models`, `schemas`, `core`, `rag`, `ai`, `db`, `auth`, `chat`, and `utils`, plus a `frontend/src` structure for pages, components, services, API clients, hooks, store, layouts, and types. FastAPI exposes versioned async endpoints, OpenAPI schemas, dependency injection, and health checks. Domain services own business rules while repositories own persistence.

This matches the requested project structure and keeps a first deployment simpler than separate microservices. Background workers remain separately scalable processes with shared domain contracts.

### 2. React/Vite frontend with server-state and UI-state separation

Use React with TypeScript and Vite, Material UI for accessible components, TanStack Query for API/server state, and Zustand only for local session, filter, and chat presentation state. The initial pages are Dashboard, Resume Upload, Job Description Management, Candidate Matching, Chat Assistant, and Admin.

TanStack Query is preferred over duplicating server data in a global store because cache invalidation and operation polling are server concerns. Next.js is not selected because the requested workflow is an authenticated application rather than an SEO-oriented site.

### 3. PostgreSQL as system of record and pgvector as initial vector store

Use SQLAlchemy models and migrations for `users`, `employees`, `resumes`, `job_descriptions`, `candidate_matches`, `chat_history`, and `audit_logs`, with supporting tables for source versions, document chunks, processing operations, refresh tokens, match runs, evidence, feedback, and outbox events. Store original files in private object storage and parsed text/metadata in PostgreSQL. Store embeddings and searchable chunk metadata in pgvector.

Use HNSW or the selected pgvector index strategy after load testing, with metadata indexes for tenant, active version, processing status, and document type. A `VectorStore` interface isolates pgvector from a future Qdrant implementation. Keeping transactional state in PostgreSQL avoids making the vector index responsible for lifecycle, authorization, or audit semantics.

### 4. Versioned asynchronous ingestion

Uploads accept only PDF, DOCX, and TXT after size, content, and malware validation. A durable operation performs extraction, normalization into resume/job metadata, chunking with source offsets, embedding generation, and vector persistence. The latest successful version is promoted atomically; failed or stale versions remain traceable but are not eligible for matching.

The pipeline uses provider interfaces so parsers, embedding models, and external services can be tested with fakes. The initial embedding adapter uses `BAAI/bge-large-en-v1.5` or a compatible configured model through Sentence Transformers.

### 5. RAG matching and provider adapters

Matching retrieves a finalized job, creates a requirement representation, filters eligible active resumes, performs pgvector semantic search, aggregates top-k chunks per employee, and invokes a constrained LLM reasoning service. LangChain is used for prompt/model orchestration, not for unbounded autonomous actions. The typed response contains rank, employee name, normalized match score, matching skills, missing skills, experience comparison, explanation, evidence references, and model/policy versions.

Define `BaseLLMProvider` with `OpenAIProvider` and `AzureOpenAIProvider` adapters. Provider responses must pass schema and evidence validation before persistence. The chat service routes requests such as best-fit searches, required-skill filters, top-N requests, and ranking explanations through the same retrieval and matching services.

### 6. JWT authentication, RBAC, and auditability

Implement login, refresh, logout, bcrypt password hashing, access-token validation, refresh-token rotation/revocation, and role dependencies for HR Admin, Recruiter, and Viewer. Enforce resource scope and role permissions at the API boundary and service layer. Record uploads, reads, edits, deletes, matches, chat requests, exports, and administrative actions in append-only audit logs with actor, target, timestamp, result, and correlation ID.

### 7. API and operation contract

Expose the required endpoints: `POST /resumes/upload`, `GET /resumes`, `GET /resumes/{id}`, `DELETE /resumes/{id}`, `POST /jobs/upload`, `POST /jobs/create`, `GET /jobs`, `POST /match`, `POST /chat`, `GET /chat/history`, and `GET /health`. Use typed request/response schemas, pagination, idempotency keys for mutating submissions, consistent error envelopes, and operation status for work that exceeds the interactive budget. OpenAPI examples and authentication requirements are part of the API documentation deliverable.

### 8. Delivery, deployment, and observability

Provide Docker Compose for frontend, backend, worker, PostgreSQL with pgvector, and supporting dependencies. Keep Kubernetes manifests or deployment templates ready for horizontal scaling. GitHub Actions runs formatting, linting, type checks, Pytest, Vitest, integration tests, build checks, and security checks. Expose structured redacted logs, Prometheus metrics, Grafana dashboards, queue health, dependency latency, retrieval quality, groundedness, and error tracking hooks.

## Risks / Trade-offs

- [Model bias or unsupported reasoning] -> Exclude protected attributes, validate evidence references, expose missing skills and confidence, retain model/policy versions, and require human review.
- [Sensitive data leakage through logs or model providers] -> Redact logs, use private storage, apply least privilege, configure approved provider settings, and test access boundaries.
- [Extraction quality varies by PDF/DOCX/TXT input] -> Preserve originals, add format fixtures, expose failures, allow retry/reprocessing, and let HR review extracted job text.
- [pgvector relevance or latency at 10,000+ resumes] -> Index active chunks, filter by tenant/readiness before similarity search, bound top-k, load test HNSW/IVF choices, and retain the vector abstraction.
- [Five-second target conflicts with cold model or embedding latency] -> Precompute document embeddings, cache safe repeated queries, stream or poll long operations, instrument provider latency, and define the normal-query budget explicitly.
- [JWT refresh-token compromise] -> Hash refresh tokens at rest, rotate and revoke them, use short-lived access tokens, enforce secure cookie or transport policy, and audit authentication events.
- [Premature complexity] -> Begin as a modular deployment with one PostgreSQL system of record and worker processes; split services only after measured operational need.
- [Retention deletion misses derived artifacts] -> Track source-to-chunk-to-embedding-to-result lineage and run reconciliation checks across PostgreSQL, object storage, and pgvector.

## Migration Plan

1. Create the monorepo structure, environment contract, Docker Compose services, health endpoint, CI checks, and baseline documentation.
2. Deploy PostgreSQL/pgvector migrations, SQLAlchemy models, JWT/RBAC, audit logging, object storage integration, and admin seed flow with matching disabled.
3. Enable resume and job ingestion, parsing, metadata review, chunking, embedding, and vector indexing; validate PDF/DOCX/TXT fixtures and retry behavior.
4. Enable offline retrieval and matching evaluation, including RAG/vector-search tests, groundedness checks, latency measurement, and a 10,000-resume load scenario.
5. Enable the frontend repository, matching, chat, and admin views for a tenant-scoped pilot; collect reviewer feedback and monitor Prometheus/Grafana signals.
6. Roll out progressively. Disable new match runs through a feature flag for rollback while preserving auditable completed results and model/policy versions.
