"""
Health Router

Exposes liveness and readiness endpoints so orchestrators (Kubernetes,
Docker Compose, load balancers) can verify the service is running and
its dependencies are reachable.
"""

from __future__ import annotations

import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.models.response_models import APIResponse, HealthResponse, ServiceStatus
from app.services.qdrant_service import QdrantService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])

# Module-level startup time used to calculate uptime
_START_TIME: float = time.monotonic()


# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------


def get_qdrant_service() -> QdrantService:
    return QdrantService()


def get_llm_service(settings: Annotated[Settings, Depends(get_settings)]) -> LLMService:
    return LLMService(provider=settings.LLM_PROVIDER)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/live",
    summary="Liveness probe",
    description="Returns 200 if the process is alive. No dependency checks.",
    response_model=APIResponse[dict],
    status_code=200,
)
async def liveness() -> APIResponse[dict]:
    """
    Liveness probe.

    Kubernetes / load balancers hit this endpoint to decide whether
    to restart the container. It should always return 200 as long as
    the event loop is running.
    """
    return APIResponse(
        success=True,
        message="Service is alive.",
        data={"status": "alive"},
    )


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Returns 200 when all critical dependencies are reachable.",
    response_model=APIResponse[HealthResponse],
    responses={
        200: {"description": "All dependencies healthy"},
        503: {"description": "One or more dependencies unavailable"},
    },
)
async def readiness(
    settings: Annotated[Settings, Depends(get_settings)],
    qdrant: QdrantService = Depends(get_qdrant_service),
) -> JSONResponse:
    """
    Readiness probe.

    Checks connectivity to every downstream service. Returns HTTP 503
    if any critical service is unavailable, so the load balancer can
    temporarily stop routing traffic to this instance.
    """
    uptime = round(time.monotonic() - _START_TIME, 3)
    service_statuses: list[ServiceStatus] = []
    overall_healthy = True

    # --- Qdrant ---
    t0 = time.monotonic()
    qdrant_ok = qdrant.ping()
    qdrant_latency = round((time.monotonic() - t0) * 1000, 2)
    service_statuses.append(
        ServiceStatus(
            name="qdrant",
            status="ok" if qdrant_ok else "unavailable",
            latency_ms=qdrant_latency,
            detail=None if qdrant_ok else "Could not reach Qdrant server.",
        )
    )
    if not qdrant_ok:
        overall_healthy = False

    # --- LLM provider (non-critical: degraded, not unhealthy) ---
    try:
        llm = LLMService(provider=settings.LLM_PROVIDER)
        t0 = time.monotonic()
        llm_ok = llm.ping()
        llm_latency = round((time.monotonic() - t0) * 1000, 2)
        service_statuses.append(
            ServiceStatus(
                name=f"llm/{settings.LLM_PROVIDER}",
                status="ok" if llm_ok else "degraded",
                latency_ms=llm_latency,
                detail=None if llm_ok else "LLM provider unreachable (non-critical).",
            )
        )
    except Exception as exc:
        logger.warning("LLM provider check failed: %s", exc)
        service_statuses.append(
            ServiceStatus(
                name=f"llm/{settings.LLM_PROVIDER}",
                status="degraded",
                detail=str(exc),
            )
        )

    overall_status = "healthy" if overall_healthy else "unhealthy"

    health = HealthResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=uptime,
        services=service_statuses,
    )

    http_status = 200 if overall_healthy else 503
    body = APIResponse(
        success=overall_healthy,
        message="All systems operational." if overall_healthy else "One or more services are unavailable.",
        data=health,
    )

    return JSONResponse(
        status_code=http_status,
        content=body.model_dump(mode="json"),
    )


@router.get(
    "",
    summary="Basic health check",
    description="Alias for /health/live — returns app name, version, and environment.",
    response_model=APIResponse[dict],
    status_code=200,
)
async def health_root(
    settings: Annotated[Settings, Depends(get_settings)],
) -> APIResponse[dict]:
    """Simple root health endpoint for quick manual checks."""
    return APIResponse(
        success=True,
        message="AI Study Companion backend is running.",
        data={
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "uptime_seconds": round(time.monotonic() - _START_TIME, 3),
        },
    )
