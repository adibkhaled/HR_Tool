## 1. Phase 1: Architecture and project setup

- [x] 1.1 Create the clean-architecture monorepo structure for `backend/app`, `frontend/src`, `infra/docker`, `infra/kubernetes`, `docs`, and test suites; verify expected directories and ownership boundaries exist.
- [x] 1.2 Configure FastAPI, React/Vite/TypeScript, Material UI, TanStack Query, Zustand, SQLAlchemy, Alembic, Pytest, Vitest, linting, formatting, and type checks; verify dependency installation and baseline tests succeed.
- [x] 1.3 Add environment configuration and secret validation for database, pgvector, JWT, object storage, embedding model, LLM providers, CORS, and observability; verify missing required production settings fail safely at startup.
- [x] 1.4 Add `/health`, `/ready`, OpenAPI metadata, correlation IDs, structured redacted logging, and a system architecture document; verify health distinguishes process readiness from dependency readiness.

## 2. Phase 2: Database, schema, and authentication

- [x] 2.1 Implement SQLAlchemy models and Alembic migrations for `users`, `employees`, `resumes`, `job_descriptions`, `candidate_matches`, `chat_history`, `audit_logs`, source versions, document chunks, processing operations, match runs, evidence, feedback, refresh tokens, and outbox events; verify migrations apply and roll back on a clean PostgreSQL/pgvector instance.
- [x] 2.2 Add ERD, relationship, index, constraint, lifecycle-state, and pgvector index documentation; verify the delivered ERD matches migration metadata and includes tenant, readiness, active-version, and vector-search indexes.
- [x] 2.3 Implement JWT login, refresh, logout, bcrypt password hashing, refresh-token rotation/revocation, and role dependencies for HR Admin, Recruiter, and Viewer; verify authentication and token-replay tests pass.
- [x] 2.4 Implement object-level authorization, safe error envelopes, append-only audit logging, and configurable retention/deletion lineage; verify cross-scope requests are denied without resource disclosure and derived artifacts are reconciled after deletion.

## 3. Phase 3: Resume upload and repository

- [ ] 3.1 Implement `POST /resumes/upload` for PDF, DOCX, and TXT with size/type/content validation, safe storage, employee metadata, idempotency, and operation status; verify accepted files create one repository record and invalid files create no searchable record.
- [ ] 3.2 Implement `GET /resumes`, `GET /resumes/{id}`, and `DELETE /resumes/{id}` with pagination, filtering, archive/delete lifecycle, authorization, and processing status; verify API contract tests cover all roles and error states.
- [ ] 3.3 Implement document extraction, text normalization, metadata parsing, chunking with source offsets, embedding generation, and pgvector persistence for resume versions; verify PDF, DOCX, and TXT fixtures become ready only after successful indexing.
- [ ] 3.4 Build the resume upload page with drag-and-drop, progress, validation errors, upload history, metadata editing, and retry/reprocess states; verify Vitest and accessibility tests cover keyboard, mobile, and failure flows.

## 4. Phase 4: Job description repository

- [ ] 4.1 Implement `POST /jobs/upload`, `POST /jobs/create`, and `GET /jobs` for document upload and finalized structured jobs with PDF, DOCX, and TXT support; verify extracted content, metadata, pagination, and authorization contracts.
- [ ] 4.2 Implement editable job drafts, explicit finalization, version replacement, archive, deletion, structured fields, chunking, embeddings, and readiness state; verify unfinalized or failed jobs cannot start a match.
- [ ] 4.3 Implement chat-assisted job authoring with conversation persistence and draft generation; verify chat output remains editable and cannot become matchable without explicit finalization.
- [ ] 4.4 Build the job management page for upload, draft editing, chat creation, metadata review, finalization, processing status, and history; verify Vitest tests cover successful and failed document workflows.

## 5. Phase 5: Vector search and RAG pipeline

- [ ] 5.1 Implement `VectorStore` and embedding-provider interfaces with a pgvector adapter and configurable BAAI/bge-large-en-v1.5 or compatible Sentence Transformer model; verify provider contract tests cover dimensions, batching, timeout, and retry behavior.
- [ ] 5.2 Implement metadata-filtered similarity search over active, ready resume chunks with tenant, document, and eligibility filters; verify vector-search tests return relevant top-k chunks and never return archived or unauthorized data.
- [ ] 5.3 Implement job requirement extraction, deterministic policy filtering, candidate aggregation, and bounded retrieval; verify protected attributes are excluded and fixed model/index versions produce reproducible retrieval fixtures.
- [ ] 5.4 Implement LangChain-based RAG orchestration with typed output validation, source evidence references, score normalization, missing skills, matching skills, experience comparison, explanation, confidence, and degradation state; verify malformed or unsupported LLM claims are rejected or flagged.

## 6. Phase 6: AI candidate ranking and APIs

- [ ] 6.1 Implement `BaseLLMProvider`, `OpenAIProvider`, and `AzureOpenAIProvider` adapters with configurable models, timeouts, retries, token limits, and redacted diagnostics; verify fake-provider tests cover success, timeout, malformed output, and outage behavior.
- [ ] 6.2 Implement `POST /match` with idempotency, asynchronous operation status, ranked results, no-suitable-candidate behavior, evidence, model/policy versions, and immutable result snapshots; verify end-to-end matching tests pass with deterministic providers.
- [ ] 6.3 Implement candidate result retrieval, evidence inspection, feedback capture, and audit events; verify reviewers can trace every displayed signal to source content without changing the original result.
- [ ] 6.4 Build the candidate matching page for job selection, run progress, ranked candidate cards/table, score breakdown, matched/missing skills, experience comparison, AI explanation, evidence, and human-review messaging; verify responsive and accessibility tests pass.

## 7. Phase 7: Chat assistant

- [ ] 7.1 Implement `POST /chat` and `GET /chat/history` with conversation persistence, authorization, request validation, citations/evidence, top-N filters, skill filters, and ranking-comparison intents; verify representative prompts return grounded structured responses.
- [ ] 7.2 Build the Chat Assistant page with conversation history, streaming or polling state, loading/error/degraded states, candidate result links, and evidence references; verify Vitest tests cover the required example interactions.

## 8. Phase 8: Frontend dashboard and administration

- [ ] 8.1 Build the Dashboard with total employees, total jobs, total matches, processing health, and recent activity; verify metrics respect the signed-in user scope and loading/error states are handled.
- [ ] 8.2 Build Admin views for user management, role assignment, audit-log search, retention configuration, and provider/operation health; verify HR Admin-only actions and audit events are enforced.
- [ ] 8.3 Add shared layout, navigation, API client, auth/session handling, route guards, design tokens, responsive behavior, and accessible Material UI patterns; verify frontend type checks, linting, and accessibility checks pass.

## 9. Phase 9: Testing, observability, and scale

- [ ] 9.1 Add backend unit, API contract, repository, authentication, authorization, extraction, RAG, vector-search, and lifecycle tests; verify Pytest passes with external providers replaced by fakes.
- [ ] 9.2 Add frontend Vitest component/page tests and end-to-end tests for upload, job creation, matching, chat, and admin flows; verify tests cover success, validation, unauthorized, processing, and degraded states.
- [ ] 9.3 Add Prometheus metrics, Grafana dashboards, dependency latency, queue depth, processing failures, match latency, groundedness, retrieval quality, result distributions, and security alerts; verify correlation IDs connect requests, workers, and audit records.
- [ ] 9.4 Add load and resilience tests for 10,000+ resumes, concurrent uploads, vector search, concurrent match/chat requests, worker restarts, provider timeouts, retries, and duplicate idempotency keys; verify normal-query latency targets and bounded resource use are measured.

## 10. Phase 10: Docker, CI/CD, and documentation

- [ ] 10.1 Create Docker Compose for frontend, backend, worker, PostgreSQL with pgvector, and required dependencies; verify a clean machine can start the stack and complete a health-check smoke test.
- [ ] 10.2 Add Kubernetes-ready manifests or deployment templates for API, worker, frontend, PostgreSQL/pgvector integration, secrets, migrations, autoscaling, and health probes; verify manifests pass schema validation without exposing secrets.
- [ ] 10.3 Add GitHub Actions for dependency installation, linting, formatting, Python type checks, frontend type checks, Pytest, Vitest, integration tests, build artifacts, and security scanning; verify the workflow runs on pull requests and main-branch changes.
- [ ] 10.4 Publish API request/response examples, setup guide, architecture diagrams, ERD, RAG sequence diagram, deployment guide, operator runbooks, privacy/retention notes, and design-decision record; verify documentation links resolve and examples match generated OpenAPI schemas.
- [ ] 10.5 Run staging security, privacy, accessibility, contract, end-to-end, evaluation, and load gates, then enable a tenant-scoped pilot with rollback controls; verify new matching can be disabled while completed results and audit history remain readable.
