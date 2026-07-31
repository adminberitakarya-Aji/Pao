"""Metrics Middleware for Memory Engine."""

import time
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from pao_shared.observability import get_meter

_meter = get_meter()

# Metrics
_request_count = _meter.create_counter(
    "http_requests_total", "Total HTTP requests", {"method", "path", "status"}
)
_request_duration = _meter.create_histogram(
    "http_request_duration_seconds", "HTTP request duration"
)
_request_size = _meter.create_histogram(
    "http_request_size_bytes", "HTTP request size in bytes"
)
_response_size = _meter.create_histogram(
    "http_response_size_bytes", "HTTP response size in bytes"
)
_active_requests = _meter.create_up_down_counter(
    "http_active_requests", "Active HTTP requests"
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting HTTP metrics.
    
    Collects:
    - Request count by method, path, status
    - Request duration histogram
    - Request/response size histograms
    - Active request gauge
    """
    
    def __init__(self, app, excluded_paths: Optional[list] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/health", "/metrics"]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip metrics for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Increment active requests
        _active_requests.add(1)
        
        # Get request size
        request_size = 0
        if request.headers.get("content-length"):
            try:
                request_size = int(request.headers["content-length"])
            except ValueError:
                pass
        
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
        except Exception as e:
            _active_requests.add(-1)
            # Record error metrics
            _request_count.add(1, {
                "method": request.method,
                "path": request.url.path,
                "status": "500",
            })
            raise
        
        # Calculate duration
        duration = time.perf_counter() - start_time
        
        # Decrement active requests
        _active_requests.add(-1)
        
        # Get response size
        response_size = 0
        if response.headers.get("content-length"):
            try:
                response_size = int(response.headers["content-length"])
            except ValueError:
                pass
        
        # Record metrics
        status = str(response.status_code)
        
        _request_count.add(1, {
            "method": request.method,
            "path": request.url.path,
            "status": status,
        })
        
        _request_duration.record(duration, {
            "method": request.method,
            "path": request.url.path,
        })
        
        if request_size > 0:
            _request_size.record(request_size, {
                "method": request.method,
                "path": request.url.path,
            })
        
        if response_size > 0:
            _response_size.record(response_size, {
                "method": request.method,
                "path": request.url.path,
            })
        
        return response
