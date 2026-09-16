## Why

HR teams need a reliable way to turn resume and job-description data into actionable candidate shortlists. Today, without a centralized repository and explainable AI matching workflow, search is manual, inconsistent, and difficult to scale across thousands of documents. This change establishes the product and technical foundation for an AI-assisted talent matching platform.

## Why

HR teams need a production-ready way to turn resume and job-description data into explainable candidate shortlists. Manual review is inconsistent and does not scale to 10,000 or more resumes, while ungrounded AI recommendations would be unsafe for employment workflows. This change establishes a secure, human-reviewed talent matching platform with a conversational interface and a RAG-based matching workflow.

## What Changes

- Add a centralized resume repository for PDF, DOCX, and TXT files, preserving originals and storing employee metadata such as name, email, phone, skills, experience, education, certifications, and upload date.
- Add a job-description repository for PDF, DOCX, and TXT uploads plus chat-assisted authoring, with metadata for title, department, required skills, experience, location, and creation date.
- Add asynchronous document parsing, text normalization, chunking, Sentence Transformer embeddings, metadata persistence, and vector indexing for resumes and jobs.
- Add an AI matching workflow that performs semantic retrieval, top-k candidate selection, LLM analysis, ranking, skill overlap, missing-skill detection, experience comparison, and grounded explanations.
- Add a conversational HR assistant for natural-language matching, filtering, top-N requests, candidate comparisons, and ranking explanations through the same RAG pipeline.
- Add role-based access using JWT authentication with HR Admin, Recruiter, and Viewer roles, plus audit logging for sensitive operations.
- Add a React and TypeScript HR application with dashboard, resume upload, job management, candidate matching, chat assistant, and administration views.
- Add documented APIs, PostgreSQL persistence with SQLAlchemy and pgvector, provider abstractions for embeddings and LLMs, Docker-based local deployment, CI/CD, tests, and observability.
- Target normal interactive queries under five seconds and scale repository operations and asynchronous matching to at least 10,000 resumes.

## Capabilities

### New Capabilities

- `talent-matching-platform`: Manage resume and job repositories, provide conversational HR search, and generate explainable ranked employee matches using a secure RAG-based AI workflow.

### Modified Capabilities

None. The repository contains no existing capability specifications.

## Impact

- Introduces a React/Vite/TypeScript frontend and a modular asynchronous FastAPI backend with OpenAPI documentation and dependency injection.
- Introduces PostgreSQL with SQLAlchemy ORM and pgvector, object storage for originals, durable processing infrastructure, and an abstract vector repository.
- Introduces LangChain orchestration, a configurable open-source embedding adapter using BAAI/bge-large-en-v1.5 or a compatible model, and `BaseLLMProvider`, OpenAI, and Azure OpenAI adapters.
- Establishes API contracts including `POST /resumes/upload`, `GET /resumes`, `GET /resumes/{id}`, `DELETE /resumes/{id}`, `POST /jobs/upload`, `POST /jobs/create`, `GET /jobs`, `POST /match`, `POST /chat`, `GET /chat/history`, and `GET /health`.
- Introduces schema, ERD, indexes, constraints, integration tests, RAG/vector-search tests, Vitest frontend tests, Docker Compose, deployment manifests, GitHub Actions, Prometheus/Grafana metrics, and operational documentation.
- Requires configurable retention and jurisdiction policy before production deployment; this change does not authorize automated hiring decisions or employment actions.
