"""FastAPI application entrypoint for DecisionAI backend."""
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import get_api_router
from app.config import settings
from app.utils.logging import get_logger, setup_logging

setup_logging()
logger = get_logger("app.main")


class AuditMiddleware(BaseHTTPMiddleware):
    """Logs every request and captures audit metadata."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        elapsed = round((time.time() - start) * 1000, 2)
        logger.info(
            "%s %s -> %s (%sms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{settings.app_name} API",
        description="Autonomous AI Business Analyst - Backend API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AuditMiddleware)

    api_router = get_api_router()
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["Health"])
    def health():
        return {"status": "healthy", "app": settings.app_name, "env": settings.app_env}

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s | path=%s", exc, request.url.path, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc)},
        )

    return app


app = create_app()
