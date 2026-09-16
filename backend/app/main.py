from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from backend.app.api.middleware import CorrelationIdMiddleware
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    yield


app = FastAPI(
    title="HR Talent Matching Platform API",
    description="Secure, evidence-based talent matching services for human-reviewed HR workflows.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(CorrelationIdMiddleware)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["system"])
async def ready(request: Request) -> JSONResponse:
    settings = get_settings()
    dependency_status = {
        "database": bool(settings.database_url),
        "pgvector": settings.pgvector_enabled,
    }
    is_ready = all(dependency_status.values())
    body = {"status": "ready" if is_ready else "not_ready", "dependencies": dependency_status}
    return JSONResponse(
        status_code=status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=body,
        headers={"X-Correlation-ID": request.state.correlation_id},
    )
