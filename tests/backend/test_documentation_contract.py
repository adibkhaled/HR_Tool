from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app

ROOT = Path(__file__).parents[2]


def test_documentation_links_and_api_examples_have_local_targets() -> None:
    readme = (ROOT / "README.md").read_text()
    for target in ("docs/setup.md", "docs/api-examples.md", "docs/architecture.md", "docs/erd.md", "docs/rag-sequence.md", "docs/deployment.md", "docs/operator-runbook.md", "docs/privacy-retention.md"):
        assert f"]({target})" in readme
        assert (ROOT / target).is_file()

    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]
    assert "/resumes/upload" in paths
    assert "/jobs/create" in paths
    assert "/jobs/{job_id}/finalize" in paths
    assert "/match" in paths