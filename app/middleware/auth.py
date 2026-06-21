from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param
from app.core.security import verify_token
from app.core.exceptions import AuthenticationError
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware to verify JWT tokens"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security = HTTPBearer()
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        if self.is_public_endpoint(request.url.path):
            return await call_next(request)
        
        # Get authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            return await call_next(request)
        
        scheme, token = get_authorization_scheme_param(authorization)
        if scheme.lower() != "bearer":
            return await call_next(request)
        
        # Verify token
        user_id = verify_token(token)
        if user_id:
            request.state.user_id = user_id
        
        return await call_next(request)
    
    def is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (doesn't require authentication)"""
        public_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
            "/api/v1/help/faq",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/openapi.json",
            "/static",
            "/health",
            "/"
        ]
        
        return any(path.startswith(public_path) for public_path in public_paths)