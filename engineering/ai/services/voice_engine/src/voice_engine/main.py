"""Main entry point for Voice Engine."""

import asyncio
import logging
import sys
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from voice_engine.config import settings
from voice_engine.api.routes import router as api_router
from voice_engine.services.voice_service import get_voice_service, close_voice_service


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.environment == "production" else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Voice Engine", version="0.1.0", environment=settings.environment)

    # Initialize voice service (loads models, connects to services)
    try:
        await get_voice_service()
        logger.info("Voice service initialized")
    except Exception as e:
        logger.error("Failed to initialize voice service", error=str(e))
        raise

    # Start background tasks
    cleanup_task = asyncio.create_task(periodic_cleanup())
    logger.info("Background tasks started")

    yield

    # Shutdown
    logger.info("Shutting down Voice Engine")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

    await close_voice_service()
    logger.info("Shutdown complete")


async def periodic_cleanup():
    """Periodic cleanup of expired sessions."""
    while True:
        try:
            await asyncio.sleep(300)  # Every 5 minutes
            service = await get_voice_service()
            if service.streaming_service:
                cleaned = await service.streaming_service.cleanup_expired_sessions(300)
                if cleaned > 0:
                    logger.info("Cleaned up expired streaming sessions", count=cleaned)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Error in periodic cleanup", error=str(e))


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="PAO Voice Engine",
        description="STT (Whisper), TTS (Kokoro/XTTS), Streaming, Interruption, LiveKit Integration",
        version="0.1.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment == "development" else ["https://app.pao.ai"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Prometheus metrics middleware
    if settings.metrics_enabled:
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000
        logger.info(
            "HTTP request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration, 2),
        )
        return response

    # Include API routes
    app.include_router(api_router)

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "service": "voice-engine",
            "version": "0.1.0",
            "status": "running",
            "docs": "/docs",
            "health": "/api/v1/health/live",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    # Configure logging for uvicorn
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["default"],
        },
    })

    uvicorn.run(
        "voice_engine.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )