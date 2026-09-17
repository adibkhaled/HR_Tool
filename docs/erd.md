# Entity relationship and lifecycle notes

```mermaid
erDiagram
    TENANT ||--o{ USER : scopes
    TENANT ||--o{ EMPLOYEE : owns
    EMPLOYEE ||--o{ RESUME : has
    RESUME ||--o{ SOURCE_VERSION : versions
    JOB_DESCRIPTION ||--o{ SOURCE_VERSION : versions
    SOURCE_VERSION ||--o{ DOCUMENT_CHUNK : indexes
    JOB_DESCRIPTION ||--o{ MATCH_RUN : receives
    MATCH_RUN ||--o{ CANDIDATE_MATCH : contains
    CANDIDATE_MATCH ||--o{ MATCH_EVIDENCE : cites
    CANDIDATE_MATCH ||--o{ MATCH_FEEDBACK : receives
    USER ||--o{ AUDIT_LOG : creates
```

All tenant-owned operational records carry `tenant_id`. Readiness and active-version state are application fields used to exclude drafts, failed versions, archived resumes, and stale vectors from retrieval. Database migrations in `backend/alembic/versions` are the schema source of truth; `backend/app/models/models.py` mirrors the tables and indexes. Vector records retain document IDs and source offsets for evidence lineage.
