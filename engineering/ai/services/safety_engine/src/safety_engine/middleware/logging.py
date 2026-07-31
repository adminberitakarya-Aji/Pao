"""
Logging Middleware.

Structured request/response logging with correlation IDs.
"""

import logging
import time
import uuid
from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/health/live",
            "/health/ready",
            "/metrics",
        ]
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        
        # Log request
        start_time = time.time()
        
        # Extract request info
        request_info = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", ""),
            "correlation_id": correlation_id,
        }
        
        # Add user/service info if available
        if hasattr(request.state, "token_data"):
            token = request.state.token_data
            request_info["user_id"] = token.user_id
            request_info["companion_id"] = token.companion_id
            request_info["service_name"] = token.service_name
        
        logger.info("Request started", extra={"request": request_info})
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            response_info = {
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "correlation_id": correlation_id,
            }
            
            # Add response size if available
            if hasattr(response, "headers"):
                content_length = response.headers.get("Content-Length")
                if content_length:
                    response_info["response_size_bytes"] = int(content_length)
            
            # Determine log level based on status code
            if response.status_code >= 500:
                logger.error("Request completed with server error", extra={"request": request_info, "response": response_info})
            elif response.status_code >= 400:
                logger.warning("Request completed with client error", extra={"request": request_info, "response": response_info})
            else:
                logger.info("Request completed successfully", extra={"request": request_info, "response": response_info})
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Response-Time-MS"] = str(round(duration_ms, 2))
            
            return response
            
        except Exception as e:
            # Log exception
            duration_ms = (time.time() - start_time) * 1000
            logger.exception(
                "Request failed with exception",
                extra={
                    "request": request_info,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                    "correlation_id": correlation_id,
                }
            )
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers (proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        if request.client:
            return request.client.host
        
        return "unknown"