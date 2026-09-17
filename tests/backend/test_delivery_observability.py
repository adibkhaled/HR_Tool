from __future__ import annotations

from time import perf_counter

from fastapi.testclient import TestClient

from backend.app.core.metrics import metrics_registry
from backend.app.main import app
from backend.app.rag.vector_store import HashEmbeddingProvider, InMemoryVectorStore, VectorRecord
from backend.app.services.repository import repository_service


def reset_repository() -> None:
    repository_service.resumes.clear()
    repository_service.jobs.clear()
    repository_service.idempotency.clear()
    repository_service.operations.clear()
    repository_service.matches.clear()
    repository_service.evidence.clear()
    repository_service.audit_log.clear()
    repository_service.chat_history.clear()
    repository_service.vector_store.records.clear()
    metrics_registry.reset()


def test_correlation_links_request_operation_and_audit_record() -> None:
    reset_repository()
    headers = {"X-Tenant-ID": "tenant-observe", "X-Role": "Recruiter", "X-Correlation-ID": "corr-123"}
    with TestClient(app) as client:
        response = client.post(
            "/resumes/upload",
            files={"file": ("resume.txt", b"Ada Skills: Python", "text/plain")},
            data={"employee_name": "Ada"},
            headers=headers,
        )
        operation = client.get(f"/operations/{response.json()['operation_id']}", headers=headers)
        metrics = client.get("/metrics", headers=headers)

    assert response.headers["X-Correlation-ID"] == "corr-123"
    assert operation.json()["correlation_id"] == "corr-123"
    assert "hr_tool_uploads_total 1" in metrics.text


def test_bounded_vector_search_handles_ten_thousand_fake_records() -> None:
    store = InMemoryVectorStore()
    provider = HashEmbeddingProvider(dimension=8)
    vector = provider.embed(["Python SQL"])[0]
    store.upsert(
        VectorRecord(str(index), "tenant-load", f"resume-{index}", "resume", "Python SQL", vector)
        for index in range(10_000)
    )

    started = perf_counter()
    results = store.similarity_search(vector, tenant_id="tenant-load", top_k=20)
    elapsed = perf_counter() - started

    assert len(results) == 20
    assert elapsed < 5
    assert all(record.tenant_id == "tenant-load" for record, _ in results)


def test_duplicate_upload_key_does_not_create_duplicate_work() -> None:
    reset_repository()
    headers = {"X-Tenant-ID": "tenant-resilience", "X-Role": "Recruiter", "Idempotency-Key": "same-upload"}
    with TestClient(app) as client:
        first = client.post(
            "/resumes/upload",
            files={"file": ("resume.txt", b"Ada Skills: Python", "text/plain")},
            data={"employee_name": "Ada"},
            headers=headers,
        )
        replay = client.post(
            "/resumes/upload",
            files={"file": ("resume.txt", b"Ada Skills: Python", "text/plain")},
            data={"employee_name": "Ada"},
            headers=headers,
        )

    assert replay.json()["id"] == first.json()["id"]
    assert len(repository_service.resumes) == 1
    assert len(repository_service.operations) == 1
