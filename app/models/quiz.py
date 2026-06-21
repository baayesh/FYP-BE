from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Numeric, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple-choice"
    TRUE_FALSE = "true-false"
    SHORT_ANSWER = "short-answer"

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    duration = Column(Integer, nullable=False)  # in minutes
    passing_score = Column(Integer, default=70)
    max_attempts = Column(Integer, default=3)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    course = relationship("Course")
    questions = relationship("QuizQuestion", back_populates="quiz")
    attempts = relationship("QuizAttempt", back_populates="quiz")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    type = Column(Enum(QuestionType), nullable=False)
    options = Column(JSON)  # Array of options for multiple choice
    correct_answer = Column(Text, nullable=False)
    points = Column(Integer, default=1)
    explanation = Column(Text)
    order_index = Column(Integer, nullable=False)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, default=func.now())
    submitted_at = Column(DateTime)
    score = Column(Numeric(5, 2))
    passed = Column(Boolean)
    answers = Column(JSON)  # Array of {questionId, answer}

    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("User")