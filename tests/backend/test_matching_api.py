from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.repository import repository_service


def setup_function() -> None:
    repository_service.resumes.clear()
    repository_service.jobs.clear()
    repository_service.idempotency.clear()
    repository_service.vector_store.records.clear()
    repository_service.matches.clear()
    repository_service.chat_history.clear()
    repository_service.feedback.clear()


def headers() -> dict[str, str]:
    return {"X-Tenant-ID": "tenant-a", "X-Role": "Recruiter"}


def test_match_requires_finalized_job_and_replays_idempotently() -> None:
    with TestClient(app) as client:
        draft = client.post("/jobs/create", json={"title": "Engineer", "description": "Skills: Python, SQL"}, headers=headers())
        blocked = client.post("/match", json={"job_id": draft.json()["id"]}, headers=headers())
        finalized = client.post(f"/jobs/{draft.json()['id']}/finalize", headers=headers())
        client.post("/resumes/upload", files={"file": ("ada.txt", b"Ada Skills: Python, SQL", "text/plain")}, data={"employee_name": "Ada"}, headers=headers())
        first = client.post("/match", json={"job_id": finalized.json()["id"]}, headers={**headers(), "Idempotency-Key": "match-1"})
        replay = client.post("/match", json={"job_id": finalized.json()["id"]}, headers={**headers(), "Idempotency-Key": "match-1"})

    assert blocked.status_code == 409
    assert first.status_code == 202
    assert first.json()["results"][0]["employee_name"] == "Ada"
    assert replay.json()["run_id"] == first.json()["run_id"]


def test_chat_history_and_feedback_are_scoped() -> None:
    with TestClient(app) as client:
        response = client.post("/chat", json={"prompt": "Find Python candidates", "top_n": 2}, headers=headers())
        history = client.get("/chat/history", headers=headers())
        other = client.get("/chat/history", headers={"X-Tenant-ID": "tenant-b", "X-Role": "Viewer"})

    assert response.status_code == 200
    assert response.json()["results"] == []
    assert len(history.json()["items"]) == 1
    assert other.json()["items"] == []


def test_match_rejects_idempotency_key_reuse_for_another_job_and_reports_no_suitable_candidates() -> None:
    with TestClient(app) as client:
        first_job = client.post("/jobs/create", json={"title": "Engineer", "description": "Skills: Python"}, headers=headers()).json()
        second_job = client.post("/jobs/create", json={"title": "Unrelated", "description": "Skills: Quantum"}, headers=headers()).json()
        client.post(f"/jobs/{first_job['id']}/finalize", headers=headers())
        client.post(f"/jobs/{second_job['id']}/finalize", headers=headers())
        client.post("/resumes/upload", files={"file": ("ada.txt", b"Ada Skills: Python", "text/plain")}, data={"employee_name": "Ada"}, headers=headers())
        first = client.post("/match", json={"job_id": first_job["id"]}, headers={**headers(), "Idempotency-Key": "match-2"})
        conflict = client.post("/match", json={"job_id": second_job["id"]}, headers={**headers(), "Idempotency-Key": "match-2"})

    assert first.json()["policy_version"] == "policy-v1"
    assert first.json()["results"][0]["rank"] == 1
    assert conflict.status_code == 409


def test_chat_supports_skill_filter_and_ranking_comparison_with_grounded_citations() -> None:
    with TestClient(app) as client:
        job = client.post("/jobs/create", json={"title": "Engineer", "description": "Skills: Python, SQL"}, headers=headers()).json()
        client.post(f"/jobs/{job['id']}/finalize", headers=headers())
        client.post("/resumes/upload", files={"file": ("ada.txt", b"Ada Skills: Python, SQL", "text/plain")}, data={"employee_name": "Ada"}, headers=headers())
        client.post("/resumes/upload", files={"file": ("bob.txt", b"Bob Skills: Python", "text/plain")}, data={"employee_name": "Bob"}, headers=headers())
        client.post("/match", json={"job_id": job["id"]}, headers=headers())
        comparison = client.post("/chat", json={"job_id": job["id"], "prompt": "Why does Ada rank higher than Bob?", "top_n": 2}, headers=headers())
        filtered = client.post("/chat", json={"job_id": job["id"], "prompt": "Find candidates", "skills": ["sql"], "top_n": 1}, headers=headers())

    assert comparison.status_code == 200
    assert comparison.json()["intent"] == "ranking_comparison"
    assert comparison.json()["comparison"]["higher_ranked"] == "Ada"
    assert comparison.json()["citations"]
    assert filtered.json()["results"]
    assert len(filtered.json()["results"]) == 1
    assert "sql" in filtered.json()["results"][0]["matching_skills"]
