from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class TeacherStats(Base):
    __tablename__ = "teacher_stats"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)

    total_courses = Column(Integer, default=0, nullable=False)
    total_students = Column(Integer, default=0, nullable=False)
    pending_grading = Column(Integer, default=0, nullable=False)
    upcoming_classes = Column(Integer, default=0, nullable=False)

    avg_feedback_rating = Column(Float, default=0.0, nullable=False)
    avg_grade = Column(Float, default=0.0, nullable=False)

    enrollments_today = Column(Integer, default=0, nullable=False)
    assignments_submitted_today = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_teacher_stats_teacher_date", "teacher_id", "snapshot_date"),
    )


class TeacherStatTimeseries(Base):
    __tablename__ = "teacher_stat_timeseries"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name = Column(String(50), nullable=False, index=True)  # e.g., enrollments, submissions, avg_grade, feedback
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)

    __table_args__ = (
        Index("idx_tstats_ts_teacher_metric", "teacher_id", "metric_name", "timestamp"),
    )
