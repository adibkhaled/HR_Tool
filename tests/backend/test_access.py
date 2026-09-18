import pytest

from backend.app.auth.security import (
    UserRole,
    create_access_token,
    require_roles,
    hash_password,
    verify_password,
    verify_token,
)
from backend.app.db.base import Base


def test_phase_two_models_are_registered() -> None:
    expected_tables = {
        "users",
        "employees",
        "resumes",
        "job_descriptions",
        "candidate_matches",
        "chat_history",
        "audit_logs",
        "source_versions",
        "document_chunks",
        "processing_operations",
        "match_runs",
        "evidence",
        "feedback",
        "refresh_tokens",
        "outbox_events",
    }
    assert expected_tables.issubset(Base.metadata.tables.keys())


def test_token_and_password_helpers_work() -> None:
    password_hash = hash_password("super-secret")
    assert verify_password("super-secret", password_hash)
    assert not verify_password("wrong", password_hash)

    token = create_access_token(subject="user-42", role=UserRole.HR_ADMIN)
    payload = verify_token(token)
    assert payload["sub"] == "user-42"
    assert payload["role"] == UserRole.HR_ADMIN


def test_role_required_guard_denies_forbidden_access() -> None:
    with pytest.raises(PermissionError, match="HR Admin"):
        require_roles({UserRole.HR_ADMIN}, {"sub": "user-7", "role": UserRole.RECRUITER})
