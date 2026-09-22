from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi.testclient import TestClient

from backend.app.ai.providers import LLMProviderError
from backend.app.main import app
from backend.app.rag.orchestration import aggregate_candidates, orchestrate
from backend.app.rag.pipeline import apply_policy, extract_requirements
from backend.app.rag.vector_store import HashEmbeddingProvider, InMemoryVectorStore, VectorRecord
from backend.app.services.repository import repository_service


def setup_function() -> None:
    repository_service.resumes.clear()
    repository_service.jobs.clear()
    repository_service.idempotency.clear()
    repository_service.vector_store.records.clear()


def headers(tenant: str = "tenant-a", role: str = "Recruiter") -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-Role": role}


def test_resume_upload_is_idempotent_and_tenant_scoped() -> None:
    with TestClient(app) as client:
        files = {"file": ("resume.txt", b"Ada has Skills: Python, SQL", "text/plain")}
        first = client.post("/resumes/upload", files=files, data={"employee_name": "Ada"}, headers={**headers(), "Idempotency-Key": "same"})
        second = client.post("/resumes/upload", files=files, data={"employee_name": "Ada"}, headers={**headers(), "Idempotency-Key": "same"})
        hidden = client.get("/resumes", headers=headers("tenant-b"))

    assert first.status_code == 202
    assert second.json()["id"] == first.json()["id"]
    assert hidden.json()["total"] == 0


def test_invalid_resume_and_viewer_write_are_rejected() -> None:
    with TestClient(app) as client:
        invalid = client.post("/resumes/upload", files={"file": ("resume.exe", b"bad", "application/octet-stream")}, headers=headers())
        denied = client.post("/jobs/create", json={"title": "Engineer", "description": "Python", "finalized": True}, headers=headers(role="Viewer"))

    assert invalid.status_code == 415
    assert denied.status_code == 403


def test_job_draft_requires_explicit_finalization() -> None:
    with TestClient(app) as client:
        created = client.post("/jobs/create", json={"title": "Platform Engineer", "description": "Skills: Python, SQL"}, headers=headers())
        jobs = client.get("/jobs", headers=headers())
        finalized = client.post(f"/jobs/{created.json()['id']}/finalize", headers=headers())

    assert created.json()["status"] == "draft"
    assert jobs.json()["items"][0]["status"] == "draft"
    assert finalized.json()["status"] == "ready"


def test_vector_provider_and_filters_are_deterministic() -> None:
    provider = HashEmbeddingProvider(dimension=8)
    vector = provider.embed(["Python SQL"])[0]
    store = InMemoryVectorStore()
    store.upsert([
        VectorRecord("ready", "tenant-a", "r1", "resume", "Python SQL", vector),
        VectorRecord("archived", "tenant-a", "r2", "resume", "Python SQL", vector, archived=True),
        VectorRecord("other", "tenant-b", "r3", "resume", "Python SQL", vector),
    ])

    results = store.similarity_search(vector, tenant_id="tenant-a", top_k=5)

    assert provider.embed(["Python SQL"])[0] == vector
    assert [record.id for record, _ in results] == ["ready"]

    aggregated = aggregate_candidates("Python SQL", extract_requirements("Skills: Python, SQL"), tenant_id="tenant-a", store=store, provider=provider)
    assert aggregated[0].resume_id == "r1"
    assert aggregated[0].matching_skills == ["python", "sql"]


def test_llm_outage_degrades_match_instead_of_returning_server_error() -> None:
    class FailingProvider:
        model_version = "ollama:test"

        def complete(self, prompt: str, *, max_tokens: int = 1200) -> dict[str, object]:
            raise LLMProviderError("LLM provider unavailable")

    store = InMemoryVectorStore()
    provider = HashEmbeddingProvider(dimension=8)
    vector = provider.embed(["Python SQL"])[0]
    store.upsert([VectorRecord("ready", "tenant-a", "r1", "resume", "Python SQL", vector)])

    outcome = orchestrate(
        "Python SQL",
        extract_requirements("Skills: Python, SQL"),
        tenant_id="tenant-a",
        store=store,
        provider=provider,
        llm=FailingProvider(),
    )

    assert outcome["degraded"] is True
    assert len(outcome["results"]) == 1
    assert outcome["results"][0].degraded is True


def test_requirement_extraction_excludes_protected_attributes() -> None:
    requirements = extract_requirements("Skills: Python, SQL; 5 years experience; age is not a criterion")

    assert requirements.skills == ("python", "sql")
    assert requirements.minimum_experience == 5
    assert "age" not in apply_policy("Python age ethnicity")


def test_document_formats_are_indexed_and_ready() -> None:
    docx_buffer = BytesIO()
    with ZipFile(docx_buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", "<document><p>Skills: Python, SQL</p></document>")
    pdf = b"%PDF-1.4 (Skills: Python, SQL)"

    with TestClient(app) as client:
        txt = client.post("/resumes/upload", files={"file": ("resume.txt", b"Skills: Python", "text/plain")}, data={"employee_name": "Txt"}, headers=headers())
        docx = client.post("/resumes/upload", files={"file": ("resume.docx", docx_buffer.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}, data={"employee_name": "Docx"}, headers=headers())
        pdf_result = client.post("/resumes/upload", files={"file": ("resume.pdf", pdf, "application/pdf")}, data={"employee_name": "Pdf"}, headers=headers())

    assert [response.json()["status"] for response in (txt, docx, pdf_result)] == ["ready", "ready", "ready"]
    assert len(repository_service.vector_store.records) >= 3
