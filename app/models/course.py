from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Numeric, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class CourseStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"

class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"

class LessonType(str, enum.Enum):
    VIDEO = "video"
    READING = "reading"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"

class Course(Base):
    __tablename__ = "courses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    level = Column(String(50))  # Beginner, Intermediate, Advanced
    duration = Column(String(50))  # e.g., "12 weeks", "8 weeks"
    thumbnail = Column(Text)
    status = Column(Enum(CourseStatus), default=CourseStatus.DRAFT)
    code = Column(String(50), nullable=True)  # Course code e.g., MATH301
    instructor = Column(String(255), nullable=True)  # Instructor name
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    teacher = relationship("User", back_populates="courses")
    enrollments = relationship("CourseEnrollment", back_populates="course")
    lessons = relationship("Lesson", back_populates="course")
    assignments = relationship("Assignment", back_populates="course")

class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    enrollment_date = Column(DateTime, default=func.now())
    status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE)
    progress = Column(Numeric(5, 2), default=0)

    # Relationships
    student = relationship("User")
    course = relationship("Course", back_populates="enrollments")

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(String(36))
    title = Column(String(255), nullable=False)
    type = Column(Enum(LessonType), nullable=False)
    content = Column(Text)  # Detailed content or description
    description = Column(Text)  # Short description for listing views
    status = Column(String(20), default="unlocked")  # unlocked | locked
    duration = Column(Integer)  # in minutes (normalized value)
    duration_text = Column(String(50))  # original display value like "15 min"
    video_link = Column(String(500))  # YouTube video URL
    quizzes_json = Column(JSON, default=[])  # [{id,title,questions}]
    assignments_json = Column(JSON, default=[])  # [{id,title,dueDate}]
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    course = relationship("Course", back_populates="lessons")
    progress = relationship("LessonProgress", back_populates="lesson")

class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    time_spent = Column(Integer, default=0)  # in minutes

    # Relationships
    student = relationship("User")
    lesson = relationship("Lesson", back_populates="progress")