"""
PAO Safety Engine - Main Application Entry Point.

FastAPI application for the Safety Engine service.
Provides crisis detection, content filtering, behavioral guards, and reality anchoring.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

from safety_engine.config import get_settings
from safety_engine.api.routes import router as safety_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "safety_engine_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "safety_engine_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
)

ACTIVE_REQUESTS = Gauge(
    "safety_engine_active_requests",
    "Number of active requests",
)

SAFETY_CHECKS = Counter(
    "safety_engine_checks_total",
    "Total number of safety checks",
    ["check_type", "result"],
)

INTERVENTION_LEVEL = Counter(
    "safety_engine_interventions_total",
    "Total interventions by level",
    ["level"],
)

CRISIS_DETECTED = Counter(
    "safety_engine_crisis_detected_total",
    "Total crisis events detected",
    ["crisis_type", "risk_level"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics."""
    
    async def dispatch(self, request: Request, call_next):
        ACTIVE_REQUESTS.inc()
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code,
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path,
            ).observe(time.time() - start_time)
            
            return response
        finally:
            ACTIVE_REQUESTS.dec()


import time


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting PAO Safety Engine...")
    
    # Initialize settings
    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Service: {settings.service_name} on port {settings.service_port}")
    
    yield
    
    logger.info("Shutting down PAO Safety Engine...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="PAO Safety Engine",
        description="Crisis detection, content filtering, behavioral guards, and reality anchoring for AI companions",
        version="1.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment == "development" else ["https://pao.app"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Metrics middleware
    app.add_middleware(MetricsMiddleware)
    
    # Include routers
    app.include_router(safety_router)
    
    # Metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        return JSONResponse(
            content=generate_latest().decode("utf-8"),
            media_type="text/plain",
        )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "service": "PAO Safety Engine",
            "version": "1.0.0",
            "status": "operational",
            "docs": "/docs",
            "metrics": "/metrics",
        }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "request_id": request.headers.get("X-Request-ID", "unknown"),
            },
        )
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "safety_engine.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )