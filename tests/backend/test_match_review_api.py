from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.repository import repository_service


def test_evidence_feedback_and_audit_are_available_without_mutating_snapshot() -> None:
    repository_service.resumes.clear()
    repository_service.jobs.clear()
    repository_service.idempotency.clear()
    repository_service.vector_store.records.clear()
    repository_service.matches.clear()
    repository_service.evidence.clear()
    repository_service.feedback.clear()
    repository_service.audit_log.clear()
    headers = {"X-Tenant-ID": "tenant-a", "X-Role": "Recruiter"}
    with TestClient(app) as client:
        job = client.post("/jobs/create", json={"title": "Engineer", "description": "Skills: Python"}, headers=headers).json()
        client.post(f"/jobs/{job['id']}/finalize", headers=headers)
        client.post("/resumes/upload", files={"file": ("ada.txt", b"Ada Skills: Python", "text/plain")}, data={"employee_name": "Ada"}, headers=headers)
        match = client.post("/match", json={"job_id": job["id"]}, headers=headers).json()
        run_id = match["run_id"]
        operation = client.get(f"/operations/{match['operation_id']}", headers=headers)
        before = client.get(f"/match/{run_id}", headers=headers).json()
        evidence = client.get(f"/match/{run_id}/evidence", headers=headers)
        feedback = client.post(f"/match/{run_id}/feedback?resume_id={before['results'][0]['resume_id']}", json={"rating": "relevant"}, headers=headers)
        after = client.get(f"/match/{run_id}", headers=headers).json()

    assert evidence.status_code == 200
    assert evidence.json()["items"]
    assert operation.json()["status"] == "completed"
    assert feedback.status_code == 201
    assert after == before
    assert {event["action"] for event in repository_service.audit_log} == {"match.completed", "match.feedback"}