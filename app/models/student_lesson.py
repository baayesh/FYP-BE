from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base

class StudentLesson(Base):
    __tablename__ = "student_lessons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    answers = Column(JSON, nullable=False)  # Maps answers to q1, q2, etc.
    question_list_1 = Column(JSON, nullable=True)  # Additional question data
    question_list_2 = Column(JSON, nullable=True)  # Additional question data
    question_list_3 = Column(JSON, nullable=True)  # Additional question data
    question_list_4 = Column(JSON, nullable=True)  # Additional question data
    Q1_Result = Column(Integer, nullable=True)  # Result for question 1
    Q2_Result = Column(Integer, nullable=True)  # Result for question 2
    Q3_Result = Column(Integer, nullable=True)  # Result for question 3
    Q4_Result = Column(Integer, nullable=True)  # Result for question 4
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    lesson = relationship("Lesson")
    student = relationship("User")
