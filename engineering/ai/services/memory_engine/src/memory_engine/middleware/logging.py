"""Logging Middleware for Memory Engine."""

import time
import uuid
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

import structlog

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request/response logging.
    
    Logs:
    - Request method, path, query params
    - Request headers (filtered)
    - Response status code
    - Latency
    - Request ID for tracing
    """
    
    def __init__(
        self, 
        app, 
        excluded_paths: Optional[list] = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
    ):
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/health", "/metrics"]
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip logging for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = request_id
        
        # Start timer
        start_time = time.perf_counter()
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            duration = time.perf_counter() - start_time
            logger.error(
                "Request failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration * 1000, 2),
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
        
        # Calculate duration
        duration = time.perf_counter() - start_time
        
        # Log response
        await self._log_response(request, response, request_id, duration)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    async def _log_request(self, request: Request, request_id: str) -> None:
        """Log incoming request."""
        # Get client info
        client_host = request.client.host if request.client else "unknown"
        client_port = request.client.port if request.client else 0
        
        # Filter sensitive headers
        headers = dict(request.headers)
        sensitive_headers = {"authorization", "x-api-key", "x-internal-api-key", "cookie", "set-cookie"}
        filtered_headers = {
            k: v for k, v in headers.items() 
            if k.lower() not in sensitive_headers
        }
        
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": client_host,
            "client_port": client_port,
            "user_agent": headers.get("user-agent"),
            "headers": filtered_headers,
        }
        
        # Add auth info if available
        if hasattr(request.state, "auth_type"):
            log_data["auth_type"] = request.state.auth_type
        if hasattr(request.state, "user_id"):
            log_data["user_id"] = request.state.user_id
        if hasattr(request.state, "service_name"):
            log_data["service_name"] = request.state.service_name
        
        logger.info("Request started", **log_data)
    
    async def _log_response(
        self, 
        request: Request, 
        response: Response, 
        request_id: str, 
        duration: float
    ) -> None:
        """Log response."""
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        }
        
        # Determine log level based on status code
        if response.status_code >= 500:
            logger.error("Request completed with server error", **log_data)
        elif response.status_code >= 400:
            logger.warning("Request completed with client error", **log_data)
        else:
            logger.info("Request completed", **log_data)