"""
Metrics Middleware.

Prometheus metrics collection for HTTP requests.
"""

import time
from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Custom registry for this service
registry = CollectorRegistry()

# Request metrics
http_requests_total = Counter(
    "safety_engine_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry,
)

http_request_duration_seconds = Histogram(
    "safety_engine_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=registry,
)

http_requests_in_progress = Gauge(
    "safety_engine_http_requests_in_progress",
    "Number of HTTP requests currently in progress",
    ["method", "endpoint"],
    registry=registry,
)

# Business metrics
safety_checks_total = Counter(
    "safety_engine_checks_total",
    "Total safety checks performed",
    ["check_type", "result"],
    registry=registry,
)

safety_check_duration_seconds = Histogram(
    "safety_engine_check_duration_seconds",
    "Safety check latency in seconds",
    ["check_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=registry,
)

safety_interventions_total = Counter(
    "safety_engine_interventions_total",
    "Total safety interventions triggered",
    ["level"],
    registry=registry,
)

safety_crisis_detected_total = Counter(
    "safety_engine_crisis_detected_total",
    "Total crisis detections",
    ["crisis_type", "risk_level"],
    registry=registry,
)

active_connections = Gauge(
    "safety_engine_active_connections",
    "Number of active WebSocket connections",
    registry=registry,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/health/live",
            "/health/ready",
            "/metrics",
        ]
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Skip metrics for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Normalize endpoint path (remove path params)
        endpoint = self._normalize_path(request.url.path)
        method = request.method
        
        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=response.status_code,
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=500,
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)
            
            raise
            
        finally:
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path by replacing path parameters with placeholders."""
        # Common patterns to normalize
        import re
        
        # Replace UUIDs
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/:uuid',
            path,
            flags=re.IGNORECASE
        )
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/:id', path)
        
        # Replace other common patterns
        path = re.sub(r'/[a-zA-Z0-9_-]{20,}', '/:param', path)
        
        return path


def record_safety_check(check_type: str, result: str, duration: float) -> None:
    """Record a safety check metric."""
    safety_checks_total.labels(check_type=check_type, result=result).inc()
    safety_check_duration_seconds.labels(check_type=check_type).observe(duration)


def record_intervention(level: str) -> None:
    """Record a safety intervention metric."""
    safety_interventions_total.labels(level=level).inc()


def record_crisis_detection(crisis_type: str, risk_level: str) -> None:
    """Record a crisis detection metric."""
    safety_crisis_detected_total.labels(crisis_type=crisis_type, risk_level=risk_level).inc()


def set_active_connections(count: int) -> None:
    """Set the number of active WebSocket connections."""
    active_connections.set(count)


def get_registry() -> CollectorRegistry:
    """Get the Prometheus registry for this service."""
    return registry