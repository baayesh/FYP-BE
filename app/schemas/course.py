from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import enum

class CourseStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"

class LessonType(str, enum.Enum):
    VIDEO = "video"
    READING = "reading"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"

# Course Base Schema
class CourseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    level: Optional[str] = Field(None, max_length=50)  # Beginner, Intermediate, Advanced
    duration: Optional[str] = Field(None, max_length=50)  # e.g., "12 weeks"
    thumbnail: Optional[str] = None

# Course Creation Schema
class CourseCreate(CourseBase):
    syllabus: Optional[List[dict]] = []

# Course Update Schema
class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    level: Optional[str] = Field(None, max_length=50)
    duration: Optional[str] = Field(None, max_length=50)
    thumbnail: Optional[str] = None
    status: Optional[CourseStatus] = None

# Lesson Schema
class LessonResponse(BaseModel):
    id: UUID
    title: str
    type: LessonType
    duration: Optional[int] = None  # in minutes
    order_index: int
    completed: Optional[bool] = False

    class Config:
        from_attributes = True

# Module Schema (for syllabus)
class ModuleResponse(BaseModel):
    id: UUID
    title: str
    order: int
    lessons: List[LessonResponse]

# Course Response Schema
class CourseResponse(CourseBase):
    id: UUID
    teacher_id: UUID
    instructor: Optional[str] = None  # Teacher name
    instructor_avatar: Optional[str] = None
    status: CourseStatus
    enrolled: Optional[int] = 0  # Number of enrolled students
    progress: Optional[float] = 0  # For student view
    total_lessons: Optional[int] = 0
    completed_lessons: Optional[int] = 0
    enrollment_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Course Detail Response (with syllabus)
class CourseDetailResponse(CourseResponse):
    syllabus: List[ModuleResponse] = []

# Course List Response
class CourseListResponse(BaseModel):
    courses: List[CourseResponse]
    pagination: Optional[dict] = None

# Course Enrollment Schema
class CourseEnrollmentResponse(BaseModel):
    enrollment_id: UUID
    message: str = "Successfully enrolled"

# Lesson Progress Schema
class LessonProgressUpdate(BaseModel):
    lesson_id: UUID
    completed: bool = True
    time_spent: int = 0  # in minutes

# Instructor Schema
class InstructorResponse(BaseModel):
    id: UUID
    name: str
    avatar: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        from_attributes = True