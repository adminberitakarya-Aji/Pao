"""Evaluation Engine - Main entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from evaluation_engine.config import settings
from evaluation_engine.api.routes import router
from evaluation_engine.services import get_evaluation_service, close_evaluation_service

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Evaluation Engine")
    await get_evaluation_service()
    yield
    logger.info("Shutting down Evaluation Engine")
    await close_evaluation_service()


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Evaluation Engine - Relationship Health Index, Drift Detection, A/B Testing, Surveys, and Reports",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "evaluation_engine.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )