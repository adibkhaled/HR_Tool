from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse

from backend.app.ai.providers import OllamaProvider, OpenAIProvider
from backend.app.api.middleware import CorrelationIdMiddleware
from backend.app.api.repositories import router as repositories_router
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.core.metrics import metrics_registry
from backend.app.services.repository import repository_service


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    if settings.llm_provider == "ollama":
        repository_service.llm = OllamaProvider(
            model=settings.llm_model,
            base_url=f"{settings.llm_base_url.rstrip('/')}/api/chat",
        )
    elif settings.llm_provider == "openai":
        repository_service.llm = OpenAIProvider(
            model=settings.llm_model,
            api_key=settings.llm_api_key.get_secret_value() if settings.llm_api_key else None,
        )
    yield


app = FastAPI(
    title="HR Talent Matching Platform API",
    description="Secure, evidence-based talent matching services for human-reviewed HR workflows.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(CorrelationIdMiddleware)
app.include_router(repositories_router)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {
        "service": "HR Talent Matching Platform API",
        "health": "/health",
        "readiness": "/ready",
        "metrics": "/metrics",
        "openapi": "/docs",
    }


@app.get("/metrics", tags=["system"], response_class=PlainTextResponse)
async def metrics() -> str:
    from backend.app.services.repository import repository_service

    ready_resumes = sum(record.status == "ready" for record in repository_service.resumes.values())
    failed_operations = sum(operation.get("status") == "failed" for operation in repository_service.operations.values())
    metrics_registry.set_gauge("hr_tool_resumes_ready", ready_resumes)
    metrics_registry.set_gauge("hr_tool_operations_failed", failed_operations)
    metrics_registry.set_gauge("hr_tool_queue_depth", sum(operation.get("status") == "processing" for operation in repository_service.operations.values()))
    metrics_registry.set_gauge("hr_tool_match_results", sum(len(match.get("results", [])) for match in repository_service.matches.values()))
    metrics_registry.set_gauge("hr_tool_grounded_results", sum(bool(match.get("results")) for match in repository_service.matches.values()))
    metrics_registry.set_gauge("hr_tool_retrieval_records", len(repository_service.vector_store.records))
    return metrics_registry.render()


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["system"])
async def ready(request: Request) -> JSONResponse:
    started = perf_counter()
    settings = get_settings()
    dependency_status = {
        "database": bool(settings.database_url),
        "pgvector": settings.pgvector_enabled,
    }
    is_ready = all(dependency_status.values())
    metrics_registry.observe("hr_tool_dependency_latency_seconds", perf_counter() - started)
    body = {"status": "ready" if is_ready else "not_ready", "dependencies": dependency_status}
    return JSONResponse(
        status_code=status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=body,
        headers={"X-Correlation-ID": request.state.correlation_id},
    )
