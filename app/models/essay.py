from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class EssayStatus(str, enum.Enum):
    NOT_STARTED = "not-started"
    IN_PROGRESS = "in-progress"
    SUBMITTED = "submitted"
    GRADED = "graded"

class EssayDifficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Essay(Base):
    __tablename__ = "essays"

    id = Column(String(36), primary_key=True, default=uuid.uuid4, index=True)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    question = Column(Text, nullable=False)
    word_limit = Column(Integer, nullable=False)
    due_date = Column(DateTime, nullable=False)
    difficulty = Column(Enum(EssayDifficulty), default=EssayDifficulty.MEDIUM)
    points = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    course = relationship("Course")
    submissions = relationship("EssaySubmission", back_populates="essay")

class EssaySubmission(Base):
    __tablename__ = "essay_submissions"

    id = Column(String(36), primary_key=True, default=uuid.uuid4, index=True)
    essay_id = Column(String(36), ForeignKey("essays.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text)
    word_count = Column(Integer)
    submitted_at = Column(DateTime)
    status = Column(Enum(EssayStatus), default=EssayStatus.NOT_STARTED)
    grade = Column(Numeric(5, 2))
    feedback = Column(Text)
    draft_saved_at = Column(DateTime)

    # Relationships
    essay = relationship("Essay", back_populates="submissions")
    student = relationship("User")