from sqlalchemy import Column, String, ForeignKey, DateTime, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class GradeItemType(str, enum.Enum):
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"
    EXAM = "exam"
    ESSAY = "essay"

class Grade(Base):
    __tablename__ = "grades"

    id = Column(String(36), primary_key=True, default=uuid.uuid4, index=True)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    item_type = Column(Enum(GradeItemType), nullable=False)
    item_id = Column(String(36), nullable=False)
    grade = Column(Numeric(5, 2), nullable=False)
    points_earned = Column(Numeric(5, 2))
    points_possible = Column(Numeric(5, 2))
    letter_grade = Column(String(2))
    graded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    graded_at = Column(DateTime, default=func.now())

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    course = relationship("Course")
    grader = relationship("User", foreign_keys=[graded_by])