from sqlalchemy import Column, String, ForeignKey, DateTime, Numeric, Integer, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class PerformanceTrend(Base):
    """
    Tracks student performance scores over time for trend analysis.
    Used for displaying performance charts in student dashboard.
    """
    __tablename__ = "performance_trends"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    score = Column(Numeric(5, 2), nullable=False)  # Overall performance score
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)  # Optional: track by course
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    course = relationship("Course", foreign_keys=[course_id])


class WeeklyActivity(Base):
    """
    Tracks student's daily/weekly activity including study hours and assignments completed.
    Used for weekly activity charts in dashboard.
    """
    __tablename__ = "weekly_activities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)  # Specific date
    day_of_week = Column(String(10), nullable=False)  # Mon, Tue, Wed, etc.
    hours_studied = Column(Numeric(4, 2), default=0.0)  # Study hours for the day
    assignments_completed = Column(Integer, default=0)  # Number of assignments completed
    quizzes_completed = Column(Integer, default=0)  # Number of quizzes completed
    lessons_viewed = Column(Integer, default=0)  # Number of lessons viewed
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    student = relationship("User", foreign_keys=[student_id])


class StudentSkill(Base):
    """
    Tracks student's skill levels across different competencies.
    Used for radar/spider charts in dashboard to show skill distribution.
    """
    __tablename__ = "student_skills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False)  # e.g., "Problem Solving", "Critical Thinking"
    skill_value = Column(Numeric(5, 2), nullable=False)  # Skill level (0-100)
    last_assessed = Column(Date, nullable=False)  # Last assessment date
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)  # Optional: skill in context of course
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    course = relationship("Course", foreign_keys=[course_id])


class StudentLevel(Base):
    """
    Tracks student's current academic level, grade, and overall progress.
    One record per student (updated as they progress).
    """
    __tablename__ = "student_levels"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    grade = Column(String(50), nullable=False)  
    stream = Column(String(50))  
    overall_progress = Column(Numeric(5, 2), default=0.0)  # Overall progress percentage (0-100)
    academic_year = Column(String(20))  # e.g., "2024-2025"
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    student = relationship("User", foreign_keys=[student_id])


class SubjectMark(Base):
    """
    Stores student's marks/scores for different subjects.
    Used for subject performance comparison charts.
    """
    __tablename__ = "subject_marks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_name = Column(String(100), nullable=False)  # e.g., "Mathematics", "Physics"
    score = Column(Numeric(5, 2), nullable=False)  # Score/Mark (0-100)
    max_score = Column(Numeric(5, 2), default=100.0)  # Maximum possible score
    assessment_type = Column(String(50))  # e.g., "Assignment", "Quiz", "Exam", "Overall"
    assessment_date = Column(Date, nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    course = relationship("Course", foreign_keys=[course_id])


class ImprovementArea(Base):
    """
    Tracks areas where students need improvement with AI-generated suggestions.
    Used for personalized recommendations in dashboard.
    """
    __tablename__ = "improvement_areas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_name = Column(String(100), nullable=False)  # Subject needing improvement
    reason = Column(Text, nullable=False)  # Why improvement is needed
    suggestion = Column(Text, nullable=False)  # AI-generated or teacher suggestion
    priority = Column(String(20), default="medium")  # low, medium, high
    status = Column(String(20), default="active")  # active, in_progress, resolved
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    identified_date = Column(Date, nullable=False)
    resolved_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    course = relationship("Course", foreign_keys=[course_id])
