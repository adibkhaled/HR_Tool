from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from backend.app.auth.security import UserRole
from backend.app.services.repository import repository_service

router = APIRouter(tags=["repositories"])
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_TYPES = {"text/plain", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


def scope(x_tenant_id: str | None, x_role: str | None) -> tuple[str, UserRole]:
    try:
        role = UserRole(x_role or UserRole.RECRUITER.value)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid role") from exc
    return x_tenant_id or "default", role


def require_write(role: UserRole) -> None:
    if role == UserRole.VIEWER:
        raise HTTPException(status_code=403, detail="This action requires Recruiter or HR Admin role")


def validate_file(upload: UploadFile, content: bytes) -> None:
    if upload.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Only PDF, DOCX, and TXT files are supported")
    if len(content) > MAX_UPLOAD_BYTES or not content:
        raise HTTPException(status_code=413, detail="File is empty or exceeds the 10 MB limit")


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    department: str | None = None
    location: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    required_experience: int | None = Field(default=None, ge=0)
    finalized: bool = False


class JobChatRequest(BaseModel):
    prompt: str = Field(min_length=1)


class MatchRequest(BaseModel):
    job_id: str
    top_k: int = Field(default=10, ge=1, le=50)


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    top_n: int = Field(default=5, ge=1, le=20)
    skills: list[str] = Field(default_factory=list, max_length=20)
    job_id: str | None = None


class FeedbackRequest(BaseModel):
    rating: str = Field(pattern="^(relevant|irrelevant|review)$")
    comment: str | None = Field(default=None, max_length=2000)


@router.post("/resumes/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_resume(file: UploadFile = File(...), employee_name: Annotated[str, Form()] = "", employee_email: Annotated[str | None, Form()] = None, employee_phone: Annotated[str | None, Form()] = None, employee_skills: Annotated[str | None, Form()] = None, idempotency_key: Annotated[str | None, Header()] = None, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:  # noqa: B008
    tenant_id, role = scope(x_tenant_id, x_role)
    require_write(role)
    content = await file.read()
    validate_file(file, content)
    try:
        return repository_service.upload_resume(tenant_id=tenant_id, file_name=file.filename or "upload", content_type=file.content_type or "", content=content, employee={"full_name": employee_name, "email": employee_email, "phone": employee_phone, "skills": employee_skills}, idempotency_key=idempotency_key)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/operations/{operation_id}")
def get_operation(operation_id: str, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:
    tenant_id, _ = scope(x_tenant_id, x_role)
    try:
        return repository_service.get_operation(tenant_id, operation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Operation not found") from exc


@router.get("/resumes")
def list_resumes(page: int = 1, page_size: int = 20, status_filter: str | None = None, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:
    tenant_id, _ = scope(x_tenant_id, x_role)
    return repository_service.list_resumes(tenant_id, status=status_filter, page=page, page_size=min(page_size, 100))


@router.get("/resumes/{resume_id}")
def get_resume(resume_id: str, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:
    tenant_id, _ = scope(x_tenant_id, x_role)
    record = repository_service.resumes.get(resume_id)
    if record is None or record.tenant_id != tenant_id or record.archived:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {"id": record.id, "tenant_id": record.tenant_id, "file_name": record.file_name, "content_type": record.content_type, "employee": record.employee, "status": record.status, "created_at": record.created_at}


@router.delete("/resumes/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(resume_id: str, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> None:
    tenant_id, role = scope(x_tenant_id, x_role)
    require_write(role)
    try:
        repository_service.delete_resume(tenant_id, resume_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Resume not found") from exc


@router.post("/jobs/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_job(file: UploadFile = File(...), title: Annotated[str, Form()] = "Untitled role", finalized: Annotated[bool, Form()] = False, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:  # noqa: B008
    tenant_id, role = scope(x_tenant_id, x_role)
    require_write(role)
    content = await file.read()
    validate_file(file, content)
    try:
        return repository_service.upload_job(tenant_id=tenant_id, file_name=file.filename or "upload", content_type=file.content_type or "", content=content, title=title, finalized=finalized)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/jobs/create", status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:
    tenant_id, role = scope(x_tenant_id, x_role)
    require_write(role)
    return repository_service.create_job(tenant_id=tenant_id, **payload.model_dump())


@router.get("/jobs")
def list_jobs(page: int = 1, page_size: int = 20, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:
    tenant_id, _ = scope(x_tenant_id, x_role)
    return repository_service.list_jobs(tenant_id, page=page, page_size=min(page_size, 100))


@router.post("/jobs/{job_id}/finalize")
def finalize_job(job_id: str, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:
    tenant_id, role = scope(x_tenant_id, x_role)
    require_write(role)
    try:
        return repository_service.finalize_job(tenant_id, job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/jobs/chat")
def author_job(payload: JobChatRequest, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:
    tenant_id, role = scope(x_tenant_id, x_role)
    require_write(role)
    return repository_service.author_job(tenant_id, payload.prompt)


@router.get("/search/resumes")
def search_resumes(query: str = "", top_k: int = 5, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:
    tenant_id, _ = scope(x_tenant_id, x_role)
    return {"items": repository_service.retrieve(tenant_id, query, top_k=min(top_k, 20))}


@router.post("/match", status_code=status.HTTP_202_ACCEPTED)
def match(payload: MatchRequest, idempotency_key: Annotated[str | None, Header()] = None, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:
    tenant_id, role = scope(x_tenant_id, x_role)
    require_write(role)
    try:
        return repository_service.run_match(tenant_id, payload.job_id, idempotency_key=idempotency_key, top_k=payload.top_k)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/match/{run_id}")
def get_match(run_id: str, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:
    tenant_id, _ = scope(x_tenant_id, x_role)
    try:
        return repository_service.get_match(tenant_id, run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Match run not found") from exc


@router.get("/match/{run_id}/evidence")
def match_evidence(run_id: str, resume_id: str | None = None, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:
    tenant_id, _ = scope(x_tenant_id, x_role)
    try:
        return {"items": repository_service.get_evidence(tenant_id, run_id, resume_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Match run not found") from exc


@router.post("/match/{run_id}/feedback", status_code=status.HTTP_201_CREATED)
def feedback(run_id: str, resume_id: str, payload: FeedbackRequest, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:
    tenant_id, role = scope(x_tenant_id, x_role)
    require_write(role)
    try:
        return repository_service.add_feedback(tenant_id, run_id, resume_id, payload.rating, payload.comment)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Match result not found") from exc


@router.post("/chat")
def chat(payload: ChatRequest, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:
    tenant_id, _ = scope(x_tenant_id, x_role)
    try:
        return repository_service.chat(tenant_id, payload.prompt, top_n=payload.top_n, skills=payload.skills, job_id=payload.job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc


@router.get("/chat/history")
def chat_history(page: int = 1, page_size: int = 50, x_tenant_id: Annotated[str | None, Header()] = None, x_role: Annotated[str | None, Header()] = None) -> dict[str, object]:
    tenant_id, _ = scope(x_tenant_id, x_role)
    items = [item for item in repository_service.chat_history if item["tenant_id"] == tenant_id]
    start = max(0, (page - 1) * page_size)
    return {"items": items[start : start + min(page_size, 100)], "page": page, "page_size": min(page_size, 100), "total": len(items)}
