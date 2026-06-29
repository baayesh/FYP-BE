from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime, time
from enum import Enum


class AttendanceStatusEnum(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class AttendanceRecordCreate(BaseModel):
    student_id: str
    status: AttendanceStatusEnum
    check_in_time: Optional[time] = None
    notes: Optional[str] = None


class AttendanceBulkCreate(BaseModel):
    course_id: str
    lesson_id: str
    date: date
    records: List[AttendanceRecordCreate]


class AttendanceRecordResponse(BaseModel):
    id: str
    student_id: str
    student_name: str
    lesson_id: str
    lesson_title: Optional[str] = None
    status: AttendanceStatusEnum
    date: date
    check_in_time: Optional[time] = None
    notes: Optional[str] = None
    marked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttendanceSummary(BaseModel):
    total: int
    present: int
    absent: int
    late: int
    excused: int
    rate: float


class AttendanceDashboard(BaseModel):
    course_id: str
    course_title: str
    lesson_id: str
    lesson_title: str
    date: date
    records: List[AttendanceRecordResponse]
    summary: AttendanceSummary


class StudentAttendanceSummary(BaseModel):
    course_id: str
    course_title: str
    total_sessions: int
    present: int
    absent: int
    late: int
    excused: int
    rate: float


class StudentAttendanceHistoryItem(BaseModel):
    id: str
    lesson_title: str
    date: date
    status: AttendanceStatusEnum
    marked_at: Optional[datetime] = None
