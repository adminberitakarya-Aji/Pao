"""Authentication Middleware for Memory Engine."""

from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication.
    
    Supports:
    - Service-to-service API keys
    - JWT token validation (for user requests)
    - Internal service authentication
    """
    
    def __init__(self, app, excluded_paths: Optional[list] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics",
        ]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip auth for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Skip auth for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Check for internal API key (service-to-service)
        internal_key = request.headers.get("X-Internal-API-Key")
        if internal_key and internal_key == settings.internal_api_key:
            request.state.auth_type = "internal"
            request.state.service_name = request.headers.get("X-Service-Name", "unknown")
            return await call_next(request)
        
        # Check for external API key
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
        if api_key and api_key == settings.api_key:
            request.state.auth_type = "api_key"
            return await call_next(request)
        
        # Check for JWT token (user authentication)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            # In production, validate JWT with jose/jwt library
            # For now, accept any bearer token in development
            if settings.environment == "development" or self._validate_jwt(token):
                request.state.auth_type = "jwt"
                request.state.user_id = self._extract_user_id(token)
                return await call_next(request)
        
        # No valid authentication
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    def _validate_jwt(self, token: str) -> bool:
        """Validate JWT token."""
        if not settings.jwt_secret:
            return False
        
        try:
            import jwt
            jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            return True
        except Exception:
            return False
    
    def _extract_user_id(self, token: str) -> Optional[str]:
        """Extract user ID from JWT token."""
        try:
            import jwt
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm], options={"verify_signature": False})
            return payload.get("sub") or payload.get("user_id")
        except Exception:
            return None