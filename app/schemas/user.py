from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import enum

class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    ADMIN = "admin"

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

# Base User Schema
class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = None
    date_of_birth: Optional[datetime] = None

# User Registration Schema
class UserRegistration(UserBase):
    password: str = Field(..., min_length=8)
    grade: Optional[str] = Field(None, max_length=50)

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

# User Login Schema
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# User Response Schema
class UserResponse(UserBase):
    id: UUID
    avatar: Optional[str] = None
    status: UserStatus
    email_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# User Profile Update Schema
class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = None
    date_of_birth: Optional[datetime] = None

# Admin User Update Schema
class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    phone: Optional[str] = Field(None, max_length=20)
    password: Optional[str] = Field(None, min_length=8)
    grade: Optional[str] = Field(None, max_length=50)

# Authentication Response Schema
class AuthResponse(BaseModel):
    success: bool = True
    data: dict

# Token Response Schema
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Password Reset Schemas
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

# User List Response (for admin)
class UserListResponse(BaseModel):
    users: List[UserResponse]
    pagination: dict

class Config:
    from_attributes = True