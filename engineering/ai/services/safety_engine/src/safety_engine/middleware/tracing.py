"""
Tracing Middleware.

OpenTelemetry distributed tracing integration.
"""

import logging
from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace
from opentelemetry.trace import SpanKind, Status, StatusCode
from opentelemetry.propagate import extract, inject
from opentelemetry.semconv.trace import HttpFlavorValues, SpanAttributes

from safety_engine.config import get_settings

logger = logging.getLogger(__name__)

# Get tracer for this service
tracer = trace.get_tracer("safety-engine")


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for distributed tracing with OpenTelemetry."""
    
    def __init__(
        self,
        app,
        exclude_paths: list = None,
        service_name: str = "safety-engine",
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/health/live",
            "/health/ready",
            "/metrics",
        ]
        self.service_name = service_name
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Skip tracing for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Extract context from headers
        context = extract(request.headers)
        
        # Create span
        span_name = f"{request.method} {request.url.path}"
        
        with tracer.start_as_current_span(
            span_name,
            context=context,
            kind=SpanKind.SERVER,
            attributes={
                SpanAttributes.HTTP_METHOD: request.method,
                SpanAttributes.HTTP_URL: str(request.url),
                SpanAttributes.HTTP_SCHEME: request.url.scheme,
                SpanAttributes.HTTP_HOST: request.url.hostname or "",
                SpanAttributes.HTTP_TARGET: request.url.path,
                SpanAttributes.HTTP_FLAVOR: HttpFlavorValues.HTTP_1_1.value,
                SpanAttributes.NET_HOST_PORT: request.url.port or (443 if request.url.scheme == "https" else 80),
                "service.name": self.service_name,
            },
        ) as span:
            # Add correlation ID if available
            correlation_id = getattr(request.state, "correlation_id", None)
            if correlation_id:
                span.set_attribute("correlation_id", correlation_id)
            
            # Add user/service context if available
            token_data = getattr(request.state, "token_data", None)
            if token_data:
                if token_data.user_id:
                    span.set_attribute("user.id", token_data.user_id)
                if token_data.companion_id:
                    span.set_attribute("companion.id", token_data.companion_id)
                if token_data.service_name:
                    span.set_attribute("service.name", token_data.service_name)
            
            # Inject trace context into request state for downstream use
            request.state.trace_context = context
            request.state.span = span
            
            try:
                response = await call_next(request)
                
                # Add response attributes
                span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, response.status_code)
                
                if response.status_code >= 500:
                    span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
                elif response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
                else:
                    span.set_status(Status(StatusCode.OK))
                
                # Inject trace context into response headers
                inject(response.headers)
                
                return response
                
            except Exception as e:
                # Record exception
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise


def get_current_span() -> trace.Span:
    """Get the current active span."""
    return trace.get_current_span()


def create_child_span(name: str, attributes: dict = None) -> trace.Span:
    """Create a child span of the current span."""
    return tracer.start_span(name, attributes=attributes or {})


def add_span_attributes(attributes: dict) -> None:
    """Add attributes to the current span."""
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


def add_span_event(name: str, attributes: dict = None) -> None:
    """Add an event to the current span."""
    span = trace.get_current_span()
    if span and span.is_recording():
        span.add_event(name, attributes or {})


def record_exception(exception: Exception) -> None:
    """Record an exception on the current span."""
    span = trace.get_current_span()
    if span and span.is_recording():
        span.record_exception(exception)


# Convenience functions for safety engine specific tracing
def trace_safety_check(check_type: str, content_length: int = None) -> trace.Span:
    """Create a span for a safety check."""
    span = tracer.start_span(
        f"safety.check.{check_type}",
        kind=SpanKind.INTERNAL,
        attributes={
            "safety.check.type": check_type,
            "safety.check.content_length": content_length or 0,
        },
    )
    return span


def trace_crisis_detection(crisis_type: str, risk_level: str) -> trace.Span:
    """Create a span for crisis detection."""
    span = tracer.start_span(
        "safety.crisis.detection",
        kind=SpanKind.INTERNAL,
        attributes={
            "safety.crisis.type": crisis_type,
            "safety.crisis.risk_level": risk_level,
        },
    )
    return span


def trace_intervention(level: str, reason: str) -> trace.Span:
    """Create a span for safety intervention."""
    span = tracer.start_span(
        "safety.intervention",
        kind=SpanKind.INTERNAL,
        attributes={
            "safety.intervention.level": level,
            "safety.intervention.reason": reason,
        },
    )
    return span


def trace_model_inference(model_name: str, input_length: int = None) -> trace.Span:
    """Create a span for model inference."""
    span = tracer.start_span(
        f"model.inference.{model_name}",
        kind=SpanKind.INTERNAL,
        attributes={
            "model.name": model_name,
            "model.input_length": input_length or 0,
        },
    )
    return span


def set_span_safety_result(span: trace.Span, passed: bool, details: dict = None) -> None:
    """Set safety check result on span."""
    if span and span.is_recording():
        span.set_attribute("safety.result.passed", passed)
        if details:
            for key, value in details.items():
                span.set_attribute(f"safety.result.{key}", value)


def set_span_error(span: trace.Span, error: Exception, message: str = None) -> None:
    """Set error status on span."""
    if span and span.is_recording():
        span.record_exception(error)
        span.set_status(Status(StatusCode.ERROR, message or str(error)))


# Context manager for manual span creation
class TraceContext:
    """Context manager for manual tracing."""
    
    def __init__(self, name: str, attributes: dict = None):
        self.name = name
        self.attributes = attributes or {}
        self.span = None
    
    def __enter__(self):
        self.span = tracer.start_span(self.name, attributes=self.attributes)
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.span.record_exception(exc_val)
            self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
        else:
            self.span.set_status(Status(StatusCode.OK))
        self.span.end()


def trace(name: str, attributes: dict = None):
    """Decorator for tracing functions."""
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with TraceContext(name, attributes):
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with TraceContext(name, attributes):
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator