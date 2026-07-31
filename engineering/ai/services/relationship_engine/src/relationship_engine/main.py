"""Relationship Engine - Main Application Entry Point."""

import logging
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Histogram, make_asgi_app

from relationship_engine.api.routes import router as api_router
from relationship_engine.config import settings
from relationship_engine.repositories.postgres import create_engine_and_session, init_db
from relationship_engine.services.relationship_service import RelationshipService
from relationship_engine.repositories.postgres import (
    PostgresRelationshipRepository,
    PostgresMilestoneRepository,
    PostgresDiaryRepository,
    PostgresStateTransitionRepository,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Metrics
REQUEST_COUNT = Counter(
    "relationship_engine_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "relationship_engine_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

# Global references for cleanup
engine = None
session_factory = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global engine, session_factory

    # Startup
    logger.info("Starting Relationship Engine...")

    # Initialize OpenTelemetry
    if settings.tracing_enabled:
        trace.set_tracer_provider(TracerProvider())
        otlp_exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
        trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info("OpenTelemetry initialized")

    # Initialize database
    engine, session_factory = await create_engine_and_session()
    await init_db()
    logger.info("Database initialized")

    # Create repositories
    relationship_repo = PostgresRelationshipRepository(session_factory)
    milestone_repo = PostgresMilestoneRepository(session_factory)
    diary_repo = PostgresDiaryRepository(session_factory)
    transition_repo = PostgresStateTransitionRepository(session_factory)

    # Create main service
    relationship_service = RelationshipService(
        relationship_repo=relationship_repo,
        milestone_repo=milestone_repo,
        diary_repo=diary_repo,
        transition_repo=transition_repo,
    )

    # Store in app state
    app.state.relationship_service = relationship_service
    app.state.session_factory = session_factory
    app.state.engine = engine

    # Instrument FastAPI
    if settings.tracing_enabled:
        FastAPIInstrumentor.instrument_app(app)
        RedisInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()
        AsyncPGInstrumentor().instrument()
        logger.info("Instrumentations enabled")

    logger.info("Relationship Engine started successfully")
    yield

    # Shutdown
    logger.info("Shutting down Relationship Engine...")
    if engine:
        await engine.dispose()
    logger.info("Relationship Engine stopped")


# Create FastAPI app
app = FastAPI(
    title="Relationship Engine",
    description="Tracks relationship dimensions, milestones, diary, and state machine",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing."""
    import time
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(process_time)

    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
    )

    return response


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Include API routes
app.include_router(api_router)


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "service": "Relationship Engine",
        "version": "0.1.0",
        "description": "Tracks relationship dimensions, milestones, diary, and state machine",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "relationship_engine.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )