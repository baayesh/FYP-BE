from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import verify_token
from app.services.auth import AuthService
from app.models.user import User, UserRole
from app.core.exceptions import AuthenticationError, AuthorizationError

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    
    if not credentials:
        raise AuthenticationError("Authentication required")
    
    user_id = verify_token(credentials.credentials)
    if not user_id:
        raise AuthenticationError("Invalid or expired token")
    
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)
    
    if not user:
        raise AuthenticationError("User not found")
    
    if user.status.value != "active":
        raise AuthenticationError("Account is inactive")
    
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    return current_user

def require_role(required_role: UserRole):
    """Dependency factory for role-based access control"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise AuthorizationError(f"Access denied. Required role: {required_role.value}")
        return current_user
    return role_checker

def require_roles(required_roles: list[UserRole]):
    """Dependency factory for multiple role-based access control"""
    def roles_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in required_roles:
            roles_str = ", ".join([role.value for role in required_roles])
            raise AuthorizationError(f"Access denied. Required roles: {roles_str}")
        return current_user
    return roles_checker

# Specific role dependencies
def get_student_user(current_user: User = Depends(require_role(UserRole.STUDENT))) -> User:
    return current_user

def get_teacher_user(current_user: User = Depends(require_role(UserRole.TEACHER))) -> User:
    return current_user

def get_parent_user(current_user: User = Depends(require_role(UserRole.PARENT))) -> User:
    return current_user

def get_admin_user(current_user: User = Depends(require_role(UserRole.ADMIN))) -> User:
    return current_user

def get_teacher_or_admin(
    current_user: User = Depends(require_roles([UserRole.TEACHER, UserRole.ADMIN]))
) -> User:
    return current_user

# Optional authentication (for public endpoints with optional user data)
def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise None"""
    
    if not credentials:
        return None
    
    user_id = verify_token(credentials.credentials)
    if not user_id:
        return None
    
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)
    
    if not user or user.status.value != "active":
        return None
    
    return user