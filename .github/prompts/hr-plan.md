You are a Senior Solution Architect, Lead Python Developer, AI Engineer, and Full Stack Engineer.

Build a production-ready HR Talent Matching Platform using a Specification Driven Development approach.

====================================================
BUSINESS OBJECTIVE
====================================================

Create an AI-powered HR system that allows HR users to:

1. Upload employee resumes.
2. Store resumes in a centralized repository.
3. Enter job descriptions through:
   - Chat interface
   - Document upload
4. Store job descriptions in a Job Repository.
5. Use an AI Agent with a RAG architecture to find the best matching employees for a given job description.
6. Display ranked employee candidates with matching scores and reasoning.

The system must support future scale to thousands of resumes and job descriptions.

====================================================
FUNCTIONAL REQUIREMENTS
====================================================

Feature 1: Resume Management

HR can upload resumes.

Supported formats:

- PDF
- DOCX
- TXT

When uploaded:

- Store original file
- Extract text
- Generate embeddings
- Store metadata

Resume metadata:

- Employee Name
- Email
- Phone
- Skills
- Years of Experience
- Education
- Certifications
- Resume Upload Date

====================================================

Feature 2: Job Description Management

HR can:

1. Upload Job Description Documents
2. Create Job Description using Chat UI

Supported formats:

- PDF
- DOCX
- TXT

Store:

- Original document
- Parsed text
- Embeddings
- Metadata

Metadata:

- Job Title
- Department
- Required Skills
- Experience Required
- Location
- Created Date

====================================================

Feature 3: AI Candidate Matching

HR asks:

"Find best candidates for this job."

System performs:

1. Retrieve job description.
2. Run semantic search against resume vectors.
3. Retrieve top matching resumes.
4. Use LLM reasoning layer.
5. Rank candidates.

Output:

- Rank
- Employee Name
- Match Score
- Matching Skills
- Missing Skills
- Experience Comparison
- AI Explanation

Example:

Candidate #1
Name: John Smith
Match Score: 91%

Matched Skills:
- Python
- Azure
- Machine Learning

Missing Skills:
- Kubernetes

Reason:
Strong AI and cloud background with 8 years experience.

====================================================

Feature 4: Chat Assistant

Provide conversational UI.

Examples:

"Who is best fit for Data Engineer role?"

"Find candidates with Python and Azure experience."

"Show top 10 candidates."

"Why is candidate A ranked higher?"

Chat should use:

RAG Pipeline
Vector Search
LLM Responses

====================================================
NON FUNCTIONAL REQUIREMENTS
====================================================

Response time:

<5 seconds for normal queries.

Support:

10,000+ resumes

Security:

Role Based Access Control

Roles:

- HR Admin
- Recruiter
- Viewer

Audit logging required.

====================================================
TECHNICAL ARCHITECTURE
====================================================

Frontend:

Use React.js with TypeScript.

Preferred Stack:

- React
- Vite
- Material UI
- TanStack Query
- Zustand State Management

Alternative:
If React is complex, generate Next.js solution.

====================================================

Backend:

Python

Framework:

FastAPI

Requirements:

- Async APIs
- OpenAPI Documentation
- Modular architecture
- Dependency Injection

====================================================

Database

PostgreSQL

Use SQLAlchemy ORM.

Tables:

users
employees
resumes
job_descriptions
candidate_matches
chat_history
audit_logs

Generate complete schema.

====================================================

Vector Database

Choose:

Option A:
pgvector inside PostgreSQL

Preferred.

Option B:
Qdrant

Abstract vector layer so it can be replaced.

====================================================

AI STACK
====================================================

Use:

- LangChain
- OpenAI compatible API
- Sentence Transformers
- pgvector

Embedding Model:

BAAI/bge-large-en-v1.5

or similar open-source embedding model.

LLM Layer:

Configurable.

Create adapter:

BaseLLMProvider

OpenAIProvider

AzureOpenAIProvider

Future providers.

====================================================
RAG PIPELINE
====================================================

Step 1:
Resume Upload

→ Parse document
→ Chunk text
→ Generate embeddings
→ Store vectors

Step 2:
Job Description Upload

→ Parse
→ Chunk
→ Generate embeddings
→ Store vectors

Step 3:
Matching

Job Description

→ Embedding
→ Vector Similarity Search

Retrieve Top K resumes

→ LLM Analysis

Return:

- Matching score
- Skill overlap
- Missing skills
- Explanation

====================================================
PROJECT STRUCTURE
====================================================

Generate clean architecture.

backend/

    app/
        api/
        services/
        repositories/
        models/
        schemas/
        core/
        rag/
        ai/
        db/
        auth/
        chat/
        utils/

frontend/

    src/
        pages/
        components/
        services/
        api/
        hooks/
        store/
        layouts/
        types/

infra/

    docker/
    kubernetes/

docs/

====================================================
API DESIGN
====================================================

Generate APIs:

POST /resumes/upload

GET /resumes

GET /resumes/{id}

DELETE /resumes/{id}

POST /jobs/upload

POST /jobs/create

GET /jobs

POST /match

POST /chat

GET /chat/history

GET /health

Provide request and response examples.

====================================================
AUTHENTICATION
====================================================

JWT Authentication.

Support:

- Login
- Refresh Token
- Logout

Password Hashing:

bcrypt

Role Based Authorization.

====================================================
FRONTEND PAGES
====================================================

1 Dashboard

Metrics:

- Total Employees
- Total Jobs
- Total Matches

2 Resume Upload

Drag & Drop

Progress Bar

Upload History

3 Job Description Management

Upload
Create via Chat

4 Candidate Matching

Select Job

Run Match

Display Ranked Results

5 Chat Assistant

Chat UI

Conversation History

6 Admin

User Management

Audit Logs

====================================================
DATABASE DESIGN
====================================================

Create ERD.

Generate:

- Tables
- Relationships
- Indexes
- Constraints

Optimize vector similarity performance.

====================================================
DEVOPS
====================================================

Provide:

Docker Compose

Containers:

- Frontend
- Backend
- PostgreSQL
- pgvector

Environment Variables

CI/CD Workflow

GitHub Actions

====================================================
TESTING
====================================================

Generate:

Backend:
- Pytest

Frontend:
- Vitest

Integration Tests

RAG Pipeline Tests

Vector Search Tests

====================================================
OBSERVABILITY
====================================================

Implement:

- Logging
- Metrics
- Error Tracking

Use:

- Prometheus
- Grafana

====================================================
IMPLEMENTATION STRATEGY
====================================================

Work in phases.

Phase 1:
Architecture & Project Setup

Phase 2:
Database

Phase 3:
Resume Upload

Phase 4:
Job Upload

Phase 5:
Vector Embeddings

Phase 6:
RAG Pipeline

Phase 7:
AI Candidate Ranking

Phase 8:
Chat Assistant

Phase 9:
Frontend

Phase 10:
Docker Deployment

For each phase:

1. Generate architecture diagrams.
2. Generate code.
3. Generate tests.
4. Generate documentation.
5. Explain design decisions.

Always follow:

- Clean Architecture
- SOLID Principles
- Repository Pattern
- Service Layer Pattern
- Domain Driven Design concepts
- Production grade coding standards

Start by generating:
1. Complete System Architecture
2. Detailed PRD
3. ERD
4. Folder Structure
5. API Specification
6. Database Schema
7. Phase 1 implementation code.