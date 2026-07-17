from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserLogin
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
