"""
Authentication Middleware.

Handles JWT validation, API key authentication, and service-to-service auth.
"""

import logging
from typing import Optional, Callable, Awaitable
from uuid import UUID

from fastapi import Request, Response, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel

from safety_engine.config import get_settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Decoded token data."""
    user_id: Optional[str] = None
    companion_id: Optional[str] = None
    service_name: Optional[str] = None
    scopes: list[str] = []
    exp: Optional[int] = None
    iat: Optional[int] = None
    jti: Optional[str] = None


class AuthMiddleware:
    """Authentication middleware for FastAPI."""
    
    def __init__(self, app=None):
        self.settings = get_settings()
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware entry point."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Skip auth for health checks and metrics
        if request.url.path in ["/health", "/health/live", "/health/ready", "/metrics"]:
            await self.app(scope, receive, send)
            return
        
        # Extract and validate token
        token_data = await self._extract_token(request)
        
        if token_data is None:
            # Allow unauthenticated access to public endpoints
            if request.url.path.startswith("/api/v1/public/"):
                await self.app(scope, receive, send)
                return
            
            # Return 401 for protected endpoints
            response = Response(
                content='{"detail": "Authentication required"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json",
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return
        
        # Add token data to request state
        request.state.token_data = token_data
        
        await self.app(scope, receive, send)
    
    async def _extract_token(self, request: Request) -> Optional[TokenData]:
        """Extract and validate token from request."""
        # Try Authorization header first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer "
            return await self._validate_token(token)
        
        # Try API key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return await self._validate_api_key(api_key)
        
        # Try service-to-service header
        service_token = request.headers.get("X-Service-Token")
        if service_token:
            return await self._validate_service_token(service_token)
        
        return None
    
    async def _validate_token(self, token: str) -> Optional[TokenData]:
        """Validate JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
                audience=self.settings.jwt_audience,
                issuer=self.settings.jwt_issuer,
            )
            
            return TokenData(
                user_id=payload.get("sub"),
                companion_id=payload.get("companion_id"),
                service_name=payload.get("service"),
                scopes=payload.get("scopes", []),
                exp=payload.get("exp"),
                iat=payload.get("iat"),
                jti=payload.get("jti"),
            )
        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            return None
    
    async def _validate_api_key(self, api_key: str) -> Optional[TokenData]:
        """Validate API key (for external integrations)."""
        # TODO: Implement API key validation against database
        # For now, check against configured keys
        if api_key in self.settings.api_keys:
            return TokenData(
                service_name="api_client",
                scopes=["safety:read", "safety:write"],
            )
        return None
    
    async def _validate_service_token(self, service_token: str) -> Optional[TokenData]:
        """Validate service-to-service token."""
        if service_token in self.settings.service_tokens:
            service_name = self.settings.service_tokens[service_token]
            return TokenData(
                service_name=service_name,
                scopes=["safety:*"],
            )
        return None


async def get_current_user(request: Request) -> TokenData:
    """
    Dependency to get current authenticated user/service.
    
    Raises:
        HTTPException: 401 if not authenticated
    """
    token_data = getattr(request.state, "token_data", None)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


async def get_current_user_id(current_user: TokenData = Depends(get_current_user)) -> UUID:
    """Dependency to get current user ID."""
    if current_user.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User context required",
        )
    return UUID(current_user.user_id)


async def get_current_companion_id(current_user: TokenData = Depends(get_current_user)) -> Optional[UUID]:
    """Dependency to get current companion ID."""
    if current_user.companion_id:
        return UUID(current_user.companion_id)
    return None


async def require_scope(required_scope: str, current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Dependency to require specific scope."""
    if required_scope not in current_user.scopes and "safety:*" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Required scope: {required_scope}",
        )
    return current_user


async def require_service_access(
    required_service: str,
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """Dependency to require access from specific service."""
    if current_user.service_name != required_service and current_user.service_name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access restricted to {required_service}",
        )
    return current_user