from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class AssignmentStatus(str, enum.Enum):
    PENDING = "pending"
    SUBMITTED = "submitted" 
    GRADED = "graded"

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    instructions = Column(Text)
    due_date = Column(DateTime, nullable=False)
    points = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    course = relationship("Course", back_populates="assignments")
    submissions = relationship("AssignmentSubmission", back_populates="assignment")

class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    assignment_id = Column(String(36), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text)
    submitted_at = Column(DateTime, default=func.now())
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.PENDING)
    grade = Column(Numeric(5, 2))
    feedback = Column(Text)

    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User")
    files = relationship("AssignmentFile", back_populates="submission")

class AssignmentEnrollment(Base):
    __tablename__ = "assignment_enrollment"

    assignment_enrollment_id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(String(100), nullable=False)
    student_id = Column(String(100), nullable=False)
    marks = Column(Integer, nullable=True)
    status = Column(String(100), nullable=True)
    assignment_id = Column(String(100), nullable=False)


class AssignmentFile(Base):
    __tablename__ = "assignment_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    submission_id = Column(String(36), ForeignKey("assignment_submissions.id", ondelete="CASCADE"), nullable=False)
    assignment_id = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_url = Column(Text, nullable=False)
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, default=func.now())

    # Relationships
    submission = relationship("AssignmentSubmission", back_populates="files")