from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_optional
from app.schemas.user import UserRegistration, UserLogin, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.common import APIResponse
from app.services.auth import AuthService
from app.core.exceptions import APIException

router = APIRouter()

@router.post("/login", response_model=APIResponse)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Authenticate user credentials and return tokens"""
    try:
        auth_service = AuthService(db)
        result = auth_service.login_user(login_data)
        
        return APIResponse(
            success=True,
            data=result
        )
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/register", response_model=APIResponse)
async def register(
    registration_data: UserRegistration,
    db: Session = Depends(get_db)
):
    """User registration endpoint"""
    try:
        auth_service = AuthService(db)
        result = auth_service.register_user(registration_data)
        
        return APIResponse(
            success=True,
            data=result
        )
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/forgot-password", response_model=APIResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Forgot password endpoint"""
    try:
        auth_service = AuthService(db)
        result = auth_service.forgot_password(request.email)
        
        return APIResponse(
            success=True,
            message=result["message"]
        )
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/reset-password", response_model=APIResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password endpoint"""
    try:
        auth_service = AuthService(db)
        result = auth_service.reset_password(request.token, request.new_password)
        
        return APIResponse(
            success=True,
            message=result["message"]
        )
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/logout", response_model=APIResponse)
async def logout(
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Logout endpoint"""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")
            
        auth_service = AuthService(db)
        result = auth_service.logout_user(str(current_user.id))
        
        return APIResponse(
            success=True,
            message=result["message"]
        )
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)