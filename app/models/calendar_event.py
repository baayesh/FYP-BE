from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class EventType(str, enum.Enum):
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"
    EXAM = "exam"
    CLASS = "class"
    EVENT = "event"

class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(String(36), primary_key=True, default=uuid.uuid4, index=True)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"))
    creator_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(Enum(EventType), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String(255))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    course = relationship("Course")
    creator = relationship("User")

# Additional models for parent-child relationships and other entities

class ParentChildRelationship(Base):
    __tablename__ = "parent_child_relationships"

    id = Column(String(36), primary_key=True, default=uuid.uuid4, index=True)
    parent_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(50), default="parent")
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    parent = relationship("User", foreign_keys=[parent_id])
    child = relationship("User", foreign_keys=[child_id])