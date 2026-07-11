from datetime import datetime, date
from typing import List, Dict

from pydantic import BaseModel


class StatPoint(BaseModel):
    timestamp: datetime
    value: float


class DistributionItem(BaseModel):
    label: str
    value: int


class CourseAvgGrade(BaseModel):
    course_id: str
    course_name: str
    avg_grade: float


class TeacherStatsSnapshot(BaseModel):
    snapshot_date: date
    total_courses: int
    total_students: int
    pending_grading: int
    upcoming_classes: int
    avg_feedback_rating: float
    avg_grade: float
    enrollments_today: int
    assignments_submitted_today: int


class TeacherDashboardStats(BaseModel):
    totals: Dict[str, int]
    charts: Dict[str, List[StatPoint]]
    distributions: Dict[str, List[DistributionItem]]
    tables: Dict[str, List[Dict]]
