from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.models.user import User, UserRole, UserStatus

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_data: dict) -> User:
        """Create a new user"""
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_all(self, 
                skip: int = 0, 
                limit: int = 100,
                role: Optional[UserRole] = None,
                status: Optional[UserStatus] = None,
                search: Optional[str] = None) -> List[User]:
        """Get all users with optional filters"""
        query = self.db.query(User)

        # Apply filters
        if role:
            query = query.filter(User.role == role)
        
        if status:
            query = query.filter(User.status == status)
        
        if search:
            search_filter = or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        return query.offset(skip).limit(limit).all()

    def count(self,
              role: Optional[UserRole] = None,
              status: Optional[UserStatus] = None,
              search: Optional[str] = None) -> int:
        """Count users with optional filters"""
        query = self.db.query(func.count(User.id))

        if role:
            query = query.filter(User.role == role)
        
        if status:
            query = query.filter(User.status == status)
        
        if search:
            search_filter = or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        return query.scalar()

    def update(self, user_id: UUID, update_data: dict) -> Optional[User]:
        """Update user by ID"""
        user = self.get_by_id(user_id)
        if not user:
            return None

        for key, value in update_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: UUID) -> bool:
        """Delete user by ID"""
        user = self.get_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        return True

    def update_last_login(self, user_id: UUID) -> Optional[User]:
        """Update user's last login timestamp"""
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.last_login = datetime.utcnow()
        self.db.commit()
        return user

    def verify_email(self, user_id: UUID) -> Optional[User]:
        """Mark user's email as verified"""
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.email_verified = True
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return user

    def change_status(self, user_id: UUID, status: UserStatus) -> Optional[User]:
        """Change user status"""
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.status = status
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return user

    def get_students(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all student users"""
        return self.db.query(User).filter(
            User.role == UserRole.STUDENT,
            User.status == UserStatus.ACTIVE
        ).offset(skip).limit(limit).all()

    def get_teachers(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all teacher users"""
        return self.db.query(User).filter(
            User.role == UserRole.TEACHER,
            User.status == UserStatus.ACTIVE
        ).offset(skip).limit(limit).all()

    def get_parents(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all parent users"""
        return self.db.query(User).filter(
            User.role == UserRole.PARENT,
            User.status == UserStatus.ACTIVE
        ).offset(skip).limit(limit).all()