"""Tracing Middleware for Memory Engine."""

from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from opentelemetry import trace
from opentelemetry.trace import SpanKind
from opentelemetry.propagate import extract, inject
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from pao_shared.observability import get_tracer

_tracer = get_tracer()
_propagator = TraceContextTextMapPropagator()


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for distributed tracing.
    
    Extracts trace context from incoming requests, creates spans for each request,
    and injects trace context into outgoing responses.
    """
    
    def __init__(self, app, excluded_paths: Optional[list] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/health", "/metrics"]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip tracing for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Extract trace context from headers
        carrier = dict(request.headers)
        ctx = extract(carrier, getter=_propagator.getter)
        
        # Create span for this request
        span_name = f"{request.method} {request.url.path}"
        
        with _tracer.start_as_current_span(
            span_name,
            context=ctx,
            kind=SpanKind.SERVER,
        ) as span:
            # Set span attributes
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.scheme", request.url.scheme)
            span.set_attribute("http.host", request.url.hostname or "")
            span.set_attribute("http.target", request.url.path)
            span.set_attribute("http.flavor", request.scope.get("http_version", "1.1"))
            
            # Add request ID if available
            if hasattr(request.state, "request_id"):
                span.set_attribute("request.id", request.state.request_id)
            
            # Add auth info if available
            if hasattr(request.state, "auth_type"):
                span.set_attribute("auth.type", request.state.auth_type)
            if hasattr(request.state, "user_id"):
                span.set_attribute("user.id", request.state.user_id)
            if hasattr(request.state, "service_name"):
                span.set_attribute("service.name", request.state.service_name)
            
            # Process request
            try:
                response = await call_next(request)
            except Exception as e:
                # Record exception on span
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
            
            # Set response attributes
            span.set_attribute("http.status_code", response.status_code)
            
            # Set span status based on HTTP status
            if response.status_code >= 500:
                span.set_status(trace.Status(trace.StatusCode.ERROR, f"HTTP {response.status_code}"))
            elif response.status_code >= 400:
                span.set_status(trace.Status(trace.StatusCode.ERROR, f"HTTP {response.status_code}"))
            
            # Inject trace context into response headers
            inject(response.headers, setter=_propagator.setter)
            
            return response