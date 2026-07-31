"""Companion Runtime - Main Application Entry Point."""

import logging
import sys
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from companion_runtime.config import settings
from companion_runtime.api.routes import router as api_router
from companion_runtime.services.runtime_service import get_runtime_service, close_runtime_service
from companion_runtime.services.state_manager import get_state_manager, close_state_manager
from companion_runtime.models.responses import HealthResponse

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Companion Runtime")
    
    # Initialize services
    try:
        runtime_service = await get_runtime_service()
        await runtime_service.initialize()
        
        state_manager = await get_state_manager()
        await state_manager.initialize()
        
        logger.info("Companion Runtime started successfully")
    except Exception as e:
        logger.error(f"Failed to start Companion Runtime: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down Companion Runtime")
    await close_runtime_service()
    await close_state_manager()
    logger.info("Companion Runtime shut down complete")


# Create FastAPI app
app = FastAPI(
    title="Companion Runtime",
    description="AI Companion Runtime - Orchestrates 8 AI engines for conversational AI",
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://app.pao.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


# Root endpoint
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - service info."""
    return HealthResponse(
        service="companion-runtime",
        version=settings.version,
        status="healthy",
        checks={"service": True},
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An internal server error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "companion_runtime.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )