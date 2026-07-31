"""Memory Engine - Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pao_shared.observability import setup_observability

from .config import settings
from .api import (
    memory_router,
    initialize_repositories,
    close_repositories,
)
from .middleware import (
    AuthMiddleware,
    LoggingMiddleware,
    MetricsMiddleware,
    TracingMiddleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_observability("memory-engine")
    await initialize_repositories()
    yield
    # Shutdown
    await close_repositories()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="PAO Memory Engine",
        description="Hybrid memory system for AI companions - episodic, semantic, and procedural memory with consolidation and recall",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )
    
    # Middleware (order matters - first added = outermost)
    app.add_middleware(TracingMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthMiddleware)
    
    # CORS (added last so it's innermost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(memory_router)
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "service": "memory-engine",
            "version": "0.1.0",
            "status": "running",
            "docs": "/docs" if settings.environment != "production" else "disabled",
        }
    
    # Health check endpoint (no auth required)
    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "memory-engine"}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "memory_engine.main:app",
        host="0.0.0.0",
        port=8004,
        reload=settings.environment == "development",
    )
