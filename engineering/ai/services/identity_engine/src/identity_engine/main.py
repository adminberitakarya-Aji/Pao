"""Identity Engine - Main entry point for the Identity Engine service."""

import asyncio
import os
import signal
import structlog
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pao_shared.config import get_settings
from pao_shared.observability import setup_logging, setup_tracing, setup_metrics

from .api.routes import router, init_services
from .services import (
    IdentityService, FingerprintService, DriftService,
    EvolutionService, ValidationService, TemplateService,
)
from .models import IdentityConfig


# Global service instances
_identity_service: Optional[IdentityService] = None
_fingerprint_service: Optional[FingerprintService] = None
_drift_service: Optional[DriftService] = None
_evolution_service: Optional[EvolutionService] = None
_validation_service: Optional[ValidationService] = None
_template_service: Optional[TemplateService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _identity_service, _fingerprint_service, _drift_service
    global _evolution_service, _validation_service, _template_service
    
    logger = structlog.get_logger(__name__)
    
    # Startup
    logger.info("Starting Identity Engine...")
    
    try:
        # Initialize shared observability
        setup_logging("identity-engine")
        setup_tracing("identity-engine")
        setup_metrics("identity-engine")
        
        # Get settings
        settings = get_settings()
        
        # Initialize services
        # In production, these would use real repositories (PostgreSQL, Redis, etc.)
        # For now, we'll use None (in-memory) or mock implementations
        
        _validation_service = ValidationService()
        
        _fingerprint_service = FingerprintService()
        
        _identity_service = IdentityService(
            repository=None,  # Would be PostgresRepository
            fingerprint_service=_fingerprint_service,
            validation_service=_validation_service,
        )
        
        _drift_service = DriftService(
            repository=None,
            fingerprint_service=_fingerprint_service,
            evolution_service=None,  # Will be set below
        )
        
        _evolution_service = EvolutionService(
            repository=None,
            fingerprint_service=_fingerprint_service,
            validation_service=_validation_service,
            identity_service=_identity_service,
        )
        
        # Wire up drift service with evolution service
        _drift_service.evolution_service = _evolution_service
        
        _template_service = TemplateService(repository=None)
        
        # Initialize API routes with services
        init_services(
            identity_service=_identity_service,
            fingerprint_service=_fingerprint_service,
            drift_service=_drift_service,
            evolution_service=_evolution_service,
            validation_service=_validation_service,
            template_service=_template_service,
        )
        
        logger.info("Identity Engine started successfully")
        
    except Exception as e:
        logger.error("Failed to start Identity Engine", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Identity Engine...")
    
    # Clean up resources
    # Close database connections, etc.
    
    logger.info("Identity Engine shut down complete")


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="Identity Engine",
        description="Companion identity management service for Pao AI platform",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routes
    app.include_router(router)
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "service": "identity-engine",
            "version": "1.0.0",
            "description": "Companion identity management service",
            "docs": "/docs",
            "health": "/identity/health",
        }
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "identity_engine.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=settings.environment == "development",
        log_config=None,  # We use structlog
    )