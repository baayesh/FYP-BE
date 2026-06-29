from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Date, Time, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(String(36), primary_key=True, default=uuid.uuid4, index=True)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(Enum(AttendanceStatus), nullable=False)
    check_in_time = Column(Time)
    notes = Column(Text)
    marked_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    marked_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("course_id", "lesson_id", "student_id", name="uq_attendance_course_lesson_student"),
    )

    # Relationships
    course = relationship("Course")
    lesson = relationship("Lesson")
    student = relationship("User", foreign_keys=[student_id])
    marker = relationship("User", foreign_keys=[marked_by])