from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# Common Response Schema
class APIResponse(BaseModel):
    success: bool = True
    data: Optional[dict] = None
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: dict

# Pagination Schema
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = "created_at"
    order: Optional[str] = Field("desc", pattern="^(asc|desc)$")

class PaginationResponse(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int

# File Upload Response
class FileUploadResponse(BaseModel):
    file_id: UUID
    filename: str
    url: str
    size: int
    content_type: str
    uploaded_at: datetime

# Dashboard Stats Schemas
class StudentDashboardStats(BaseModel):
    active_courses: int
    upcoming_assignments: int
    completed_lessons: int
    average_grade: float
    recent_activity: List[dict]

class TeacherDashboardStats(BaseModel):
    total_students: int
    active_courses: int
    pending_grading: int
    upcoming_classes: int
    recent_activity: List[dict]

# Performance Data Schema
class PerformanceData(BaseModel):
    performance_trend: List[dict]
    weekly_activity: List[dict]
    skills_data: List[dict]
    subject_scores: List[dict]

# Calendar Event Schemas
class CalendarEventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: str = Field(..., pattern="^(assignment|quiz|exam|class|event)$")
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    course_id: Optional[UUID] = None

class CalendarEventResponse(CalendarEventCreate):
    id: UUID
    creator_id: UUID
    course_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True