from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from datetime import datetime, timedelta
import uuid

from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserRegistration, UserLogin, UserResponse
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    generate_reset_token,
    validate_password
)
from app.core.exceptions import (
    AuthenticationError, 
    ValidationError, 
    ConflictError, 
    NotFoundError
)

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, user_data: UserRegistration) -> dict:
        """Register a new user"""
        
        # Validate password strength
        is_valid, errors = validate_password(user_data.password)
        if not is_valid:
            raise ValidationError("Password validation failed", {"errors": errors})

        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ConflictError("User with this email already exists")

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        
        new_user = User(
            id=uuid.uuid4(),
            email=user_data.email,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            phone=user_data.phone,
            bio=user_data.bio,
            date_of_birth=user_data.date_of_birth,
            status=UserStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        try:
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            
            return {
                "userId": str(new_user.id),
                "message": "Registration successful"
            }
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("User with this email already exists")

    def login_user(self, login_data: UserLogin) -> dict:
        """Authenticate user and return tokens"""
        
        # Find user by email
        user = self.db.query(User).filter(User.email == login_data.email).first()
        if not user:
            raise AuthenticationError("Invalid email or password")

        # Check password
        if not verify_password(login_data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationError("Account is inactive or suspended")

        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()

        # Generate tokens
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "firstName": user.first_name,
                "lastName": user.last_name,
                "role": user.role.value,
                "avatar": user.avatar,
                "phone": user.phone
            },
            "token": access_token,
            "refreshToken": refresh_token
        }

    def authenticate_user_credentials(self, email: str, password: str) -> dict:
        """Authenticate user credentials and return full user data"""
        
        # Find user by email
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise AuthenticationError("Invalid email or password")

        # Check password
        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationError("Account is inactive or suspended")

        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()

        # Return full user data (excluding password_hash for security)
        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
            "phone": user.phone,
            "avatar": user.avatar,
            "bio": user.bio,
            "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
            "status": user.status.value,
            "email_verified": user.email_verified,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            # Validate that it's a valid UUID string
            uuid.UUID(user_id)
            return self.db.query(User).filter(User.id == user_id).first()
        except ValueError:
            return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def forgot_password(self, email: str) -> dict:
        """Generate password reset token"""
        
        user = self.get_user_by_email(email)
        if not user:
            # Return success even if user doesn't exist (security best practice)
            return {"message": "Password reset link sent to email"}

        # Generate reset token (in real app, store in database with expiration)
        reset_token = generate_reset_token()
        
        # TODO: Store token in database with expiration
        # TODO: Send email with reset link
        
        return {"message": "Password reset link sent to email"}

    def reset_password(self, token: str, new_password: str) -> dict:
        """Reset password using token"""
        
        # Validate password strength
        is_valid, errors = validate_password(new_password)
        if not is_valid:
            raise ValidationError("Password validation failed", {"errors": errors})

        # TODO: Verify token from database
        # For now, assuming token is valid
        
        # In real implementation, get user_id from token in database
        # user = get_user_from_reset_token(token)
        # if not user:
        #     raise AuthenticationError("Invalid or expired reset token")
        
        # user.password_hash = get_password_hash(new_password)
        # self.db.commit()
        
        return {"message": "Password reset successful"}

    def logout_user(self, user_id: str) -> dict:
        """Logout user (in real app, invalidate tokens)"""
        
        # TODO: Add token to blacklist or invalidate in Redis
        
        return {"message": "Logged out successfully"}

    def refresh_token(self, refresh_token: str) -> dict:
        """Generate new access token from refresh token"""
        
        # TODO: Verify refresh token and generate new access token
        
        return {
            "access_token": "new_access_token",
            "token_type": "bearer"
        }