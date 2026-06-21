from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(100), nullable=False)  # LOGIN, CREATE, UPDATE, DELETE, SUBMIT, GRADE
    entity_type = Column(String(50))  # user, course, assignment, grade, etc
    entity_id = Column(String(36))
    details = Column(String(500))  # Additional context
    timestamp = Column(DateTime, default=func.now(), index=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User")
