"""
Error Handler Middleware.

Centralized error handling with structured error responses.
"""

import logging
import traceback
from typing import Callable, Awaitable

from fastapi import Request, Response, HTTPException, status
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from pydantic import ValidationError

from safety_engine.config import get_settings

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling."""
    
    def __init__(self, app, debug: bool = False):
        super().__init__(app)
        self.settings = get_settings()
        self.debug = debug or self.settings.debug
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        try:
            return await call_next(request)
            
        except HTTPException as e:
            # FastAPI HTTP exceptions - return as-is
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "code": e.status_code,
                        "message": e.detail,
                        "type": "http_error",
                    }
                },
                headers=e.headers,
            )
            
        except RequestValidationError as e:
            # Request validation errors
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": {
                        "code": 422,
                        "message": "Validation error",
                        "type": "validation_error",
                        "details": e.errors(),
                    }
                },
            )
            
        except ValidationError as e:
            # Pydantic validation errors
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": {
                        "code": 422,
                        "message": "Validation error",
                        "type": "validation_error",
                        "details": e.errors(),
                    }
                },
            )
            
        except ValueError as e:
            # Value errors (business logic)
            logger.warning(f"ValueError: {e}", extra={"path": request.url.path})
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": {
                        "code": 400,
                        "message": str(e),
                        "type": "value_error",
                    }
                },
            )
            
        except KeyError as e:
            # Missing keys
            logger.warning(f"KeyError: {e}", extra={"path": request.url.path})
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": {
                        "code": 404,
                        "message": f"Resource not found: {e}",
                        "type": "not_found",
                    }
                },
            )
            
        except PermissionError as e:
            # Permission errors
            logger.warning(f"PermissionError: {e}", extra={"path": request.url.path})
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": {
                        "code": 403,
                        "message": "Permission denied",
                        "type": "permission_error",
                    }
                },
            )
            
        except TimeoutError as e:
            # Timeout errors
            logger.error(f"TimeoutError: {e}", extra={"path": request.url.path})
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "error": {
                        "code": 504,
                        "message": "Request timeout",
                        "type": "timeout_error",
                    }
                },
            )
            
        except ConnectionError as e:
            # Connection errors (external services)
            logger.error(f"ConnectionError: {e}", extra={"path": request.url.path})
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": {
                        "code": 503,
                        "message": "Service temporarily unavailable",
                        "type": "connection_error",
                    }
                },
            )
            
        except Exception as e:
            # Unhandled exceptions
            correlation_id = getattr(request.state, "correlation_id", "unknown")
            
            # Log full traceback
            logger.exception(
                f"Unhandled exception: {type(e).__name__}: {e}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "correlation_id": correlation_id,
                }
            )
            
            # Return error response
            error_response = {
                "error": {
                    "code": 500,
                    "message": "Internal server error",
                    "type": "internal_error",
                    "correlation_id": correlation_id,
                }
            }
            
            # Include debug info in development
            if self.debug:
                error_response["error"]["debug"] = {
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                    "traceback": traceback.format_exc(),
                }
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response,
            )


class SafetyError(Exception):
    """Base exception for safety engine errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "SAFETY_ERROR",
        details: dict = None,
        status_code: int = 500,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code


class SafetyValidationError(SafetyError):
    """Safety validation error."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            error_code="SAFETY_VALIDATION_ERROR",
            details=details,
            status_code=400,
        )


class CrisisDetectedError(SafetyError):
    """Crisis detected - requires immediate attention."""
    
    def __init__(self, message: str, crisis_type: str, risk_level: str, details: dict = None):
        super().__init__(
            message=message,
            error_code="CRISIS_DETECTED",
            details={
                "crisis_type": crisis_type,
                "risk_level": risk_level,
                **(details or {}),
            },
            status_code=400,  # Not an error per se, but requires special handling
        )


class InterventionRequiredError(SafetyError):
    """Safety intervention required."""
    
    def __init__(
        self,
        message: str,
        level: str,
        reason: str,
        details: dict = None,
    ):
        super().__init__(
            message=message,
            error_code="INTERVENTION_REQUIRED",
            details={
                "intervention_level": level,
                "reason": reason,
                **(details or {}),
            },
            status_code=400,
        )


class ModelError(SafetyError):
    """ML model error."""
    
    def __init__(self, message: str, model_name: str, details: dict = None):
        super().__init__(
            message=message,
            error_code="MODEL_ERROR",
            details={
                "model_name": model_name,
                **(details or {}),
            },
            status_code=500,
        )


class ConfigurationError(SafetyError):
    """Configuration error."""
    
    def __init__(self, message: str, config_key: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={
                "config_key": config_key,
                **(details or {}),
            },
            status_code=500,
        )


def create_error_response(
    status_code: int,
    message: str,
    error_type: str,
    details: dict = None,
    correlation_id: str = None,
) -> JSONResponse:
    """Create standardized error response."""
    content = {
        "error": {
            "code": status_code,
            "message": message,
            "type": error_type,
        }
    }
    
    if details:
        content["error"]["details"] = details
    
    if correlation_id:
        content["error"]["correlation_id"] = correlation_id
    
    return JSONResponse(status_code=status_code, content=content)


async def handle_safety_exception(request: Request, exc: SafetyError) -> JSONResponse:
    """Handle safety-specific exceptions."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    logger.warning(
        f"Safety exception: {exc.error_code}: {exc.message}",
        extra={
            "path": request.url.path,
            "correlation_id": correlation_id,
            "error_code": exc.error_code,
            "details": exc.details,
        }
    )
    
    return create_error_response(
        status_code=exc.status_code,
        message=exc.message,
        error_type=exc.error_code.lower(),
        details=exc.details,
        correlation_id=correlation_id,
    )