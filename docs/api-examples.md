# API examples

All repository examples use `X-Tenant-ID` and `X-Role` in the local development profile. Production uses JWT bearer authentication.

## Upload a resume

```sh
curl -X POST http://localhost:8000/resumes/upload \
  -H 'X-Tenant-ID: default' -H 'X-Role: Recruiter' -H 'Idempotency-Key: resume-001' \
  -F employee_name=Ada -F file=@resume.txt
```

## Create, finalize, and match a job

```sh
curl -X POST http://localhost:8000/jobs/create -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: default' -H 'X-Role: Recruiter' \
  -d '{"title":"Platform Engineer","description":"Skills: Python, SQL"}'

curl -X POST http://localhost:8000/jobs/JOB_ID/finalize \
  -H 'X-Tenant-ID: default' -H 'X-Role: Recruiter'

curl -X POST http://localhost:8000/match -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: default' -H 'X-Role: Recruiter' -d '{"job_id":"JOB_ID","top_k":10}'
```

The generated OpenAPI document at `/openapi.json` is the contract source of truth. Match results contain rank, normalized score, matching and missing skills, evidence snippets, model version, policy version, and a degraded flag.
