"""
AI Study Companion — FastAPI application entry point.

Responsibilities:
  - Configure structured logging
  - Instantiate the FastAPI app with metadata
  - Register CORS middleware
  - Mount all routers
  - Expose lifespan startup / shutdown hooks
  - Provide a top-level exception handler for unhandled errors
"""

from __future__ import annotations

import logging
import logging.config
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import health, retrieval, study_plan, upload

# ---------------------------------------------------------------------------
# Settings (loaded once at import time)
# ---------------------------------------------------------------------------

settings = get_settings()


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------


def configure_logging() -> None:
    """
    Set up Python's standard logging using the level and format from settings.

    Called once before the application starts accepting requests.
    """
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": settings.LOG_FORMAT,
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": settings.LOG_LEVEL.upper(),
                "handlers": ["console"],
            },
            # Quiet down noisy third-party loggers in production
            "loggers": {
                "uvicorn": {"level": "INFO", "propagate": True},
                "uvicorn.error": {"level": "INFO", "propagate": True},
                "uvicorn.access": {"level": "WARNING", "propagate": True},
                "httpx": {"level": "WARNING", "propagate": True},
                "httpcore": {"level": "WARNING", "propagate": True},
            },
        }
    )


configure_logging()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Async context manager that runs on startup and shutdown.

    Startup:
      - Ensure the uploads directory exists.
      - (Future) warm up embedding model, verify Qdrant connectivity.

    Shutdown:
      - (Future) close connection pools, flush buffers.
    """
    # ---- Startup ----
    logger.info(
        "Starting %s v%s [%s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT.upper(),
    )

    # Ensure the upload directory exists on every start
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Upload directory ready: %s", settings.UPLOAD_DIR)

    # TODO: pre-load embedding model to avoid cold-start on first request
    # TODO: verify Qdrant connectivity and create collection if absent

    logger.info("%s is ready to accept requests.", settings.APP_NAME)

    yield  # Application runs here

    # ---- Shutdown ----
    logger.info("Shutting down %s.", settings.APP_NAME)
    # TODO: close any open resources (DB connections, HTTP clients, etc.)


# ---------------------------------------------------------------------------
# FastAPI instance
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """
    Factory function that constructs and configures the FastAPI application.

    Using a factory makes the app easy to test in isolation and avoids
    module-level side effects when importing.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # Middleware
    # ------------------------------------------------------------------

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOWED_METHODS,
        allow_headers=settings.ALLOWED_HEADERS,
    )

    # ------------------------------------------------------------------
    # Request timing middleware (lightweight, no external dependency)
    # ------------------------------------------------------------------

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        """Attach X-Process-Time (ms) to every response."""
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        response.headers["X-Process-Time"] = str(duration_ms)
        return response

    # ------------------------------------------------------------------
    # Exception handlers
    # ------------------------------------------------------------------

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Return a structured 422 body consistent with APIResponse envelope."""
        errors = [
            f"{' → '.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in exc.errors()
        ]
        logger.warning("Validation error on %s %s: %s", request.method, request.url.path, errors)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Request validation failed.",
                "data": None,
                "errors": errors,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all handler — prevents stack traces leaking to clients."""
        logger.exception(
            "Unhandled exception on %s %s: %s",
            request.method,
            request.url.path,
            exc,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "An unexpected error occurred. Please try again later.",
                "data": None,
                "errors": [str(exc)] if settings.DEBUG else None,
            },
        )

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------

    API_V1 = "/api/v1"
    API    = "/api"

    # Health and upload stay under /api/v1 only
    app.include_router(health.router,  prefix=API_V1)
    app.include_router(upload.router,  prefix=API_V1)

    # Retrieval router is mounted at both prefixes:
    #   /api    → POST /api/retrieve              (primary simple endpoint)
    #   /api/v1 → POST /api/v1/retrieval/search   (full search with filters)
    #             POST /api/v1/retrieval/ask       (RAG Q&A)
    app.include_router(retrieval.router, prefix=API)
    app.include_router(retrieval.router, prefix=API_V1)

    # Study-plan router is mounted at both prefixes:
    #   /api    → POST /api/study-plan              (primary simple endpoint)
    #   /api/v1 → POST /api/v1/study-plan/generate  (full options endpoint)
    #             POST /api/v1/study-plan/summary    (summarisation)
    #             POST /api/v1/study-plan/flashcards (flashcard generation)
    app.include_router(study_plan.router, prefix=API)
    app.include_router(study_plan.router, prefix=API_V1)

    logger.info(
        "Registered routes: %s",
        [route.path for route in app.routes if hasattr(route, "path")],  # type: ignore[union-attr]
    )

    return app


# ---------------------------------------------------------------------------
# Application singleton
# ---------------------------------------------------------------------------

app: FastAPI = create_app()


# ---------------------------------------------------------------------------
# Development entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
