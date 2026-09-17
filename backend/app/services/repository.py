from __future__ import annotations

import hashlib
import re
import uuid
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from backend.app.rag.vector_store import HashEmbeddingProvider, InMemoryVectorStore, VectorRecord
from backend.app.rag.pipeline import extract_requirements
from backend.app.rag.orchestration import orchestrate
from backend.app.services.document_pipeline import chunk_text, extract_text, parse_skills
from backend.app.core.correlation import get_correlation_id
from backend.app.core.metrics import metrics_registry


@dataclass
class ResumeRecord:
    id: str
    tenant_id: str
    file_name: str
    content_type: str
    employee: dict[str, object]
    text: str
    status: str = "ready"
    archived: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_hash: str = ""
    source_uri: str = ""
    version: int = 1
    operation_id: str = ""


@dataclass
class JobRecord:
    id: str
    tenant_id: str
    title: str
    department: str | None
    location: str | None
    required_skills: list[str]
    required_experience: int | None
    description: str
    status: str = "draft"
    archived: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: int = 1
    operation_id: str = ""
    source_uri: str = ""


class RepositoryService:
    MATCH_POLICY_VERSION = "policy-v1"
    MATCH_RELEVANCE_THRESHOLD = 0.35

    def __init__(self) -> None:
        self.resumes: dict[str, ResumeRecord] = {}
        self.jobs: dict[str, JobRecord] = {}
        self.idempotency: dict[tuple[str, str], dict[str, object]] = {}
        self.chat_history: list[dict[str, object]] = []
        self.operations: dict[str, dict[str, object]] = {}
        self.audit_log: list[dict[str, object]] = []
        self.matches: dict[str, dict[str, object]] = {}
        self.feedback: list[dict[str, object]] = []
        self.evidence: dict[str, list[dict[str, object]]] = {}
        self.llm = None
        self.embeddings = HashEmbeddingProvider()
        self.vector_store = InMemoryVectorStore()
        self.storage_root = Path("data/documents")

    def _audit(self, tenant_id: str, action: str, target_id: str, *, details: dict[str, object] | None = None) -> None:
        event = {"tenant_id": tenant_id, "action": action, "target_id": target_id, "result": "success", "correlation_id": get_correlation_id()}
        if details is not None:
            event["details"] = details
        self.audit_log.append(event)

    def upload_resume(self, *, tenant_id: str, file_name: str, content_type: str, content: bytes, employee: dict[str, object], idempotency_key: str | None) -> dict[str, object]:
        if idempotency_key and (tenant_id, idempotency_key) in self.idempotency:
            return self.idempotency[(tenant_id, idempotency_key)]
        if not employee.get("full_name", "").strip():
            raise ValueError("Employee name is required")
        text = extract_text(content, content_type)
        if not text:
            raise ValueError("The document contains no readable text")
        resume_id = str(uuid.uuid4())
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(file_name).name) or "upload"
        destination = self.storage_root / tenant_id / f"{resume_id}-{safe_name}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        operation_id = str(uuid.uuid4())
        record = ResumeRecord(resume_id, tenant_id, safe_name, content_type, {**employee, "skills": employee.get("skills") or parse_skills(text)}, text, status="processing", source_hash=hashlib.sha256(content).hexdigest(), source_uri=str(destination), operation_id=operation_id)
        self.resumes[resume_id] = record
        self.operations[operation_id] = {"id": operation_id, "type": "resume_ingestion", "status": "processing", "resource_id": resume_id, "created_at": record.created_at}
        self.operations[operation_id]["correlation_id"] = get_correlation_id()
        metrics_registry.increment("hr_tool_uploads_total")
        try:
            chunks = chunk_text(text)
            vectors = self.embeddings.embed([chunk.text for chunk in chunks])
            self.vector_store.upsert([VectorRecord(f"{resume_id}:{index}", tenant_id, resume_id, "resume", chunk.text, vector, source_offset_start=chunk.start, source_offset_end=chunk.end) for index, (chunk, vector) in enumerate(zip(chunks, vectors))])
            record.status = "ready"
            self.operations[operation_id]["status"] = "completed"
            metrics_registry.increment("hr_tool_processing_completed_total")
        except (ValueError, RuntimeError) as exc:
            record.status = "failed"
            self.operations[operation_id].update({"status": "failed", "error": str(exc)})
            metrics_registry.increment("hr_tool_processing_failed_total")
        result = {"id": resume_id, "status": record.status, "operation_id": operation_id, "employee": record.employee, "file_name": safe_name}
        if idempotency_key:
            self.idempotency[(tenant_id, idempotency_key)] = result
        return result

    def list_resumes(self, tenant_id: str, *, status: str | None = None, page: int = 1, page_size: int = 20) -> dict[str, object]:
        records = [record for record in self.resumes.values() if record.tenant_id == tenant_id and not record.archived and (status is None or record.status == status)]
        start = max(0, (page - 1) * page_size)
        return {"items": [asdict(record) for record in records[start : start + page_size]], "page": page, "page_size": page_size, "total": len(records)}

    def delete_resume(self, tenant_id: str, resume_id: str) -> None:
        record = self.resumes.get(resume_id)
        if record is None or record.tenant_id != tenant_id:
            raise KeyError(resume_id)
        record.archived = True
        record.status = "archived"
        for vector_id, vector in list(self.vector_store.records.items()):
            if vector.document_id == resume_id:
                self.vector_store.records[vector_id] = VectorRecord(**{**asdict(vector), "archived": True, "eligible": False})

    def get_operation(self, tenant_id: str, operation_id: str) -> dict[str, object]:
        operation = self.operations.get(operation_id)
        if operation is None:
            raise KeyError(operation_id)
        if operation.get("type") == "match":
            run = self.matches.get(str(operation["resource_id"]))
            job = self.jobs.get(str(run["job_id"])) if run is not None else None
            if job is None or job.tenant_id != tenant_id:
                raise KeyError(operation_id)
            return dict(operation)
        record = self.resumes.get(str(operation["resource_id"]))
        if record is None or record.tenant_id != tenant_id:
            raise KeyError(operation_id)
        return dict(operation)

    def create_job(self, *, tenant_id: str, title: str, description: str, department: str | None, location: str | None, required_skills: list[str], required_experience: int | None, finalized: bool) -> dict[str, object]:
        if finalized and not description.strip():
            raise ValueError("A finalized job requires a description")
        job = JobRecord(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            title=title,
            department=department,
            location=location,
            required_skills=[skill.lower() for skill in required_skills],
            required_experience=required_experience,
            description=description,
            status="ready" if finalized else "draft",
        )
        self.jobs[job.id] = job
        if finalized:
            self._index_job(job)
        return asdict(job)

    def _index_job(self, job: JobRecord) -> None:
        chunks = chunk_text(job.description)
        vectors = self.embeddings.embed([chunk.text for chunk in chunks])
        self.vector_store.upsert([VectorRecord(f"job:{job.id}:{index}", job.tenant_id, job.id, "job", chunk.text, vector, source_offset_start=chunk.start, source_offset_end=chunk.end) for index, (chunk, vector) in enumerate(zip(chunks, vectors))])

    def upload_job(self, *, tenant_id: str, file_name: str, content_type: str, content: bytes, title: str, finalized: bool) -> dict[str, object]:
        text = extract_text(content, content_type)
        return self.create_job(tenant_id=tenant_id, title=title, description=text, department=None, location=None, required_skills=parse_skills(text), required_experience=None, finalized=finalized)

    def list_jobs(self, tenant_id: str, *, page: int = 1, page_size: int = 20) -> dict[str, object]:
        records = [record for record in self.jobs.values() if record.tenant_id == tenant_id and not record.archived]
        start = max(0, (page - 1) * page_size)
        return {"items": [asdict(record) for record in records[start : start + page_size]], "page": page, "page_size": page_size, "total": len(records)}

    def finalize_job(self, tenant_id: str, job_id: str) -> dict[str, object]:
        job = self.jobs.get(job_id)
        if job is None or job.tenant_id != tenant_id:
            raise KeyError(job_id)
        if not job.description.strip() or not job.title.strip():
            raise ValueError("A title and description are required")
        job.status = "ready"
        self._index_job(job)
        return asdict(job)

    def author_job(self, tenant_id: str, prompt: str) -> dict[str, object]:
        title = prompt.splitlines()[0][:255] or "Untitled role"
        draft = self.create_job(tenant_id=tenant_id, title=title, description=prompt, department=None, location=None, required_skills=parse_skills(prompt), required_experience=None, finalized=False)
        self.chat_history.append({"tenant_id": tenant_id, "prompt": prompt, "job_id": draft["id"]})
        return {"draft": draft, "conversation_id": str(uuid.uuid4())}

    def run_match(self, tenant_id: str, job_id: str, *, idempotency_key: str | None = None, top_k: int = 10) -> dict[str, object]:
        started = perf_counter()
        if idempotency_key and (tenant_id, f"match:{idempotency_key}") in self.idempotency:
            replay = self.idempotency[(tenant_id, f"match:{idempotency_key}")]
            if replay.get("job_id") != job_id:
                raise ValueError("Idempotency key was already used for another job")
            return deepcopy(replay)
        job = self.jobs.get(job_id)
        if job is None or job.tenant_id != tenant_id or job.archived:
            raise KeyError(job_id)
        if job.status != "ready":
            raise ValueError("Job must be finalized and ready before matching")
        run_id = str(uuid.uuid4())
        requirements = extract_requirements(job.description)
        operation_id = str(uuid.uuid4())
        self.operations[operation_id] = {"id": operation_id, "type": "match", "status": "processing", "resource_id": run_id, "created_at": datetime.now(timezone.utc).isoformat()}
        self.operations[operation_id]["correlation_id"] = get_correlation_id()
        metrics_registry.increment("hr_tool_match_runs_total")
        outcome = orchestrate(job.description, requirements, tenant_id=tenant_id, store=self.vector_store, provider=self.embeddings, top_k=min(top_k, 50), llm=self.llm)
        results = []
        for result in sorted(outcome["results"], key=lambda item: item.normalized_score, reverse=True):
            resume = self.resumes.get(result.resume_id)
            if resume is None or resume.status != "ready" or result.normalized_score < self.MATCH_RELEVANCE_THRESHOLD:
                continue
            results.append({"resume_id": result.resume_id, "employee_name": resume.employee.get("full_name"), **result.model_dump()})
        for rank, result in enumerate(results, start=1):
            result["rank"] = rank
        model_version = getattr(self.llm, "model_version", "deterministic-llm-v1")
        response = {"run_id": run_id, "operation_id": operation_id, "job_id": job_id, "status": "completed", "degraded": bool(outcome.get("degraded")), "results": results, "model_version": model_version, "policy_version": self.MATCH_POLICY_VERSION, "relevance_threshold": self.MATCH_RELEVANCE_THRESHOLD, "no_suitable_candidates": not results}
        self.evidence[run_id] = [evidence for result in results for evidence in result.get("evidence", [])]
        self.matches[run_id] = deepcopy(response)
        self.operations[operation_id].update({"status": "completed", "run_id": run_id, "progress": 100})
        self._audit(tenant_id, "match.completed", run_id)
        metrics_registry.observe("hr_tool_match_latency_seconds", perf_counter() - started)
        metrics_registry.observe("hr_tool_match_score", sum(float(item["normalized_score"]) for item in results) / len(results) if results else 0)
        if idempotency_key:
            self.idempotency[(tenant_id, f"match:{idempotency_key}")] = deepcopy(response)
        return deepcopy(response)

    def get_match(self, tenant_id: str, run_id: str) -> dict[str, object]:
        result = self.matches.get(run_id)
        job = self.jobs.get(str(result["job_id"])) if result is not None else None
        if result is None or job is None or job.tenant_id != tenant_id:
            raise KeyError(run_id)
        return deepcopy(result)

    def get_evidence(self, tenant_id: str, run_id: str, resume_id: str | None = None) -> list[dict[str, object]]:
        self.get_match(tenant_id, run_id)
        return [item for item in self.evidence.get(run_id, []) if resume_id is None or item.get("evidence_id", "").startswith(resume_id)]

    def add_feedback(self, tenant_id: str, run_id: str, resume_id: str, rating: str, comment: str | None) -> dict[str, object]:
        result = self.get_match(tenant_id, run_id)
        if not any(item["resume_id"] == resume_id for item in result["results"]):
            raise KeyError(resume_id)
        feedback = {"id": str(uuid.uuid4()), "run_id": run_id, "resume_id": resume_id, "rating": rating, "comment": comment}
        self.feedback.append({"tenant_id": tenant_id, **feedback})
        self._audit(tenant_id, "match.feedback", run_id, details={"resume_id": resume_id, "rating": rating})
        return feedback

    def chat(self, tenant_id: str, prompt: str, *, top_n: int = 5, skills: list[str] | None = None, job_id: str | None = None) -> dict[str, object]:
        requested_skills = {skill.lower().strip() for skill in (skills or []) if skill.strip()}
        if job_id is not None:
            job = self.jobs.get(job_id)
            if job is None or job.tenant_id != tenant_id or job.archived or job.status != "ready":
                raise KeyError(job_id)
        job_id = job_id or next((job.id for job in self.jobs.values() if job.tenant_id == tenant_id and job.status == "ready" and job.title.lower() in prompt.lower()), None)
        comparison = self._ranking_comparison(tenant_id, prompt, job_id)
        if comparison is not None:
            response = {"conversation_id": str(uuid.uuid4()), "prompt": prompt, "intent": "ranking_comparison", "results": comparison["results"][:top_n], "comparison": comparison["comparison"], "degraded": False, "citations": comparison["citations"], "skills": sorted(requested_skills), "job_id": job_id}
            self._store_chat(tenant_id, response)
            return response
        if job_id is None:
            query = prompt
            requirements = extract_requirements(prompt)
            outcome = orchestrate(query, requirements, tenant_id=tenant_id, store=self.vector_store, provider=self.embeddings, top_k=min(top_n, 20))
            results = [item.model_dump() for item in outcome["results"] if item.normalized_score >= self.MATCH_RELEVANCE_THRESHOLD]
        else:
            results = self.run_match(tenant_id, job_id, top_k=50)["results"]
        if requested_skills:
            results = [item for item in results if requested_skills.issubset({skill.lower() for skill in item.get("matching_skills", [])})]
        results = results[:top_n]
        response = {"conversation_id": str(uuid.uuid4()), "prompt": prompt, "intent": "candidate_search", "results": results, "degraded": False, "citations": [item["evidence"][0] for item in results if item.get("evidence")], "skills": sorted(requested_skills), "job_id": job_id}
        self._store_chat(tenant_id, response)
        return response

    def _store_chat(self, tenant_id: str, response: dict[str, object]) -> None:
        self.chat_history.append({"tenant_id": tenant_id, **deepcopy(response)})
        self._audit(tenant_id, "chat.completed", str(response["conversation_id"]))

    def _ranking_comparison(self, tenant_id: str, prompt: str, job_id: str | None) -> dict[str, object] | None:
        lowered = prompt.lower()
        if not ("rank" in lowered and ("higher" in lowered or "above" in lowered or "why" in lowered)):
            return None
        candidates = [resume for resume in self.resumes.values() if resume.tenant_id == tenant_id and resume.status == "ready" and not resume.archived]
        mentioned = [resume for resume in candidates if str(resume.employee.get("full_name", "")).lower() in lowered]
        if len(mentioned) < 2:
            return None
        match = next((item for item in reversed(list(self.matches.values())) if item.get("job_id") == job_id and item.get("results")), None)
        if match is None:
            return None
        by_resume = {str(item["resume_id"]): item for item in match["results"]}
        ranked = [by_resume.get(resume.id) for resume in mentioned]
        ranked = [item for item in ranked if item is not None]
        if len(ranked) < 2:
            return None
        ranked.sort(key=lambda item: item["rank"])
        higher, lower = ranked[:2]
        reasons = [
            {"signal": "matching_skills", "higher": higher["matching_skills"], "lower": lower["matching_skills"]},
            {"signal": "missing_skills", "higher": higher["missing_skills"], "lower": lower["missing_skills"]},
            {"signal": "normalized_score", "higher": higher["normalized_score"], "lower": lower["normalized_score"]},
        ]
        citations = higher.get("evidence", []) + lower.get("evidence", [])
        return {"results": [higher, lower], "citations": citations, "comparison": {"higher_ranked": higher["employee_name"], "lower_ranked": lower["employee_name"], "reasons": reasons}}

    def retrieve(self, tenant_id: str, query: str, *, top_k: int = 5) -> list[dict[str, object]]:
        started = perf_counter()
        query_vector = self.embeddings.embed([query])[0]
        results = [{"resume_id": record.document_id, "text": record.text, "score": round(score, 6), "evidence_id": record.id} for record, score in self.vector_store.similarity_search(query_vector, tenant_id=tenant_id, top_k=top_k)]
        metrics_registry.observe("hr_tool_retrieval_latency_seconds", perf_counter() - started)
        metrics_registry.observe("hr_tool_retrieval_quality", sum(item["score"] for item in results) / len(results) if results else 0)
        return results


repository_service = RepositoryService()
