"""
PAO Shared Observability
OpenTelemetry tracing, metrics, and structured logging setup.
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

import structlog
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from .config import get_settings

settings = get_settings()

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)

ACTIVE_REQUESTS = Gauge(
    "http_requests_active",
    "Active HTTP requests",
    ["method", "endpoint"]
)

MODEL_INFERENCE_COUNT = Counter(
    "model_inference_total",
    "Total model inferences",
    ["model", "provider", "task_type", "status"]
)

MODEL_INFERENCE_LATENCY = Histogram(
    "model_inference_duration_seconds",
    "Model inference latency in seconds",
    ["model", "provider", "task_type"]
)

MODEL_TOKENS_USED = Counter(
    "model_tokens_total",
    "Total tokens used",
    ["model", "provider", "type"]
)

MODEL_COST_ESTIMATE = Counter(
    "model_cost_estimate_total",
    "Estimated cost in USD",
    ["model", "provider"]
)

ERROR_COUNT = Counter(
    "errors_total",
    "Total errors",
    ["service", "error_type"]
)


def setup_tracing(service_name: str, version: str = "1.0.0") -> trace.Tracer:
    """
    Initialize OpenTelemetry tracing.
    
    Args:
        service_name: Name of the service
        version: Service version
        
    Returns:
        Configured tracer
    """
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: version,
        DEPLOYMENT_ENVIRONMENT: settings.environment,
    })
    
    provider = TracerProvider(resource=resource)
    
    # OTLP exporter
    otlp_endpoint = settings.otlp_endpoint
    if otlp_endpoint:
        trace_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    
    trace.set_tracer_provider(provider)
    
    # Auto-instrumentation
    FastAPIInstrumentor.instrument()
    HTTPXClientInstrumentor.instrument()
    RedisInstrumentor.instrument()
    Psycopg2Instrumentor.instrument()
    SQLAlchemyInstrumentor.instrument()
    
    return trace.get_tracer(service_name)


def setup_metrics(service_name: str, version: str = "1.0.0") -> metrics.Meter:
    """
    Initialize OpenTelemetry metrics.
    
    Args:
        service_name: Name of the service
        version: Service version
        
    Returns:
        Configured meter
    """
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: version,
        DEPLOYMENT_ENVIRONMENT: settings.environment,
    })
    
    otlp_endpoint = settings.otlp_endpoint
    readers = []
    
    if otlp_endpoint:
        metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
        readers.append(PeriodicExportingMetricReader(metric_exporter, export_interval_millis=10000))
    
    provider = MeterProvider(resource=resource, metric_readers=readers)
    metrics.set_meter_provider(provider)
    
    return metrics.get_meter(service_name)


def setup_logging(service_name: str) -> structlog.BoundLogger:
    """
    Configure structured logging with structlog.
    
    Args:
        service_name: Name of the service
        
    Returns:
        Configured logger
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer() if settings.environment != "development" 
            else structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.environment == "development" else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    logger = structlog.get_logger(service_name)
    logger.info("Logging configured", service=service_name, environment=settings.environment)
    return logger


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


@contextmanager
def trace_span(tracer: trace.Tracer, name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Context manager for creating spans.
    
    Args:
        tracer: OpenTelemetry tracer
        name: Span name
        attributes: Optional span attributes
    """
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise


def record_request_metric(method: str, endpoint: str, status: int, duration: float):
    """Record HTTP request metrics."""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)


def record_inference_metric(
    model: str, 
    provider: str, 
    task_type: str, 
    status: str,
    duration: float,
    tokens: int,
    cost: float
):
    """Record model inference metrics."""
    MODEL_INFERENCE_COUNT.labels(
        model=model, provider=provider, task_type=task_type, status=status
    ).inc()
    MODEL_INFERENCE_LATENCY.labels(
        model=model, provider=provider, task_type=task_type
    ).observe(duration)
    MODEL_TOKENS_USED.labels(
        model=model, provider=provider, type="total"
    ).inc(tokens)
    MODEL_COST_ESTIMATE.labels(
        model=model, provider=provider
    ).inc(cost)


def record_error(service: str, error_type: str):
    """Record error metric."""
    ERROR_COUNT.labels(service=service, error_type=error_type).inc()


def metrics_endpoint() -> Response:
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Initialize on import
_tracer: Optional[trace.Tracer] = None
_meter: Optional[metrics.Meter] = None
_logger: Optional[structlog.BoundLogger] = None


def init_observability(service_name: str, version: str = "1.0.0") -> tuple:
    """
    Initialize all observability components.
    
    Returns:
        Tuple of (tracer, meter, logger)
    """
    global _tracer, _meter, _logger
    
    _tracer = setup_tracing(service_name, version)
    _meter = setup_metrics(service_name, version)
    _logger = setup_logging(service_name)
    
    return _tracer, _meter, _logger


def get_tracer() -> Optional[trace.Tracer]:
    """Get the global tracer."""
    return _tracer


def get_meter() -> Optional[metrics.Meter]:
    """Get the global meter."""
    return _meter