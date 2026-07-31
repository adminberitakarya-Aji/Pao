"""
Safety Engine Middleware Package.

Cross-cutting concerns:
- Authentication & Authorization
- Request/Response logging
- Metrics collection
- Distributed tracing
- Rate limiting
- Error handling
"""

from safety_engine.middleware.auth import AuthMiddleware, get_current_user
from safety_engine.middleware.logging import LoggingMiddleware
from safety_engine.middleware.metrics import MetricsMiddleware
from safety_engine.middleware.tracing import TracingMiddleware
from safety_engine.middleware.rate_limit import RateLimitMiddleware
from safety_engine.middleware.error_handler import ErrorHandlerMiddleware

__all__ = [
    "AuthMiddleware",
    "get_current_user",
    "LoggingMiddleware",
    "MetricsMiddleware",
    "TracingMiddleware",
    "RateLimitMiddleware",
    "ErrorHandlerMiddleware",
]