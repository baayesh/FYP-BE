from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


# ===== Performance Trend Schemas =====
class PerformanceTrendBase(BaseModel):
    date: date
    score: Decimal = Field(..., ge=0, le=100, description="Performance score (0-100)")
    course_id: Optional[str] = None


class PerformanceTrendCreate(PerformanceTrendBase):
    student_id: str


class PerformanceTrendUpdate(BaseModel):
    score: Optional[Decimal] = Field(None, ge=0, le=100)
    date: Optional[date] = None
    course_id: Optional[str] = None


class PerformanceTrendResponse(PerformanceTrendBase):
    id: str
    student_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Weekly Activity Schemas =====
class WeeklyActivityBase(BaseModel):
    date: date
    day_of_week: str = Field(..., pattern="^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)$")
    hours_studied: Decimal = Field(default=0.0, ge=0, le=24)
    assignments_completed: int = Field(default=0, ge=0)
    quizzes_completed: int = Field(default=0, ge=0)
    lessons_viewed: int = Field(default=0, ge=0)


class WeeklyActivityCreate(WeeklyActivityBase):
    student_id: str


class WeeklyActivityUpdate(BaseModel):
    date: Optional[date] = None
    hours_studied: Optional[Decimal] = Field(None, ge=0, le=24)
    assignments_completed: Optional[int] = Field(None, ge=0)
    quizzes_completed: Optional[int] = Field(None, ge=0)
    lessons_viewed: Optional[int] = Field(None, ge=0)


class WeeklyActivityResponse(WeeklyActivityBase):
    id: str
    student_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Student Skill Schemas =====
class StudentSkillBase(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=100)
    skill_value: Decimal = Field(..., ge=0, le=100, description="Skill level (0-100)")
    last_assessed: date
    course_id: Optional[str] = None


class StudentSkillCreate(StudentSkillBase):
    student_id: str


class StudentSkillUpdate(BaseModel):
    skill_name: Optional[str] = Field(None, min_length=1, max_length=100)
    skill_value: Optional[Decimal] = Field(None, ge=0, le=100)
    last_assessed: Optional[date] = None
    course_id: Optional[str] = None


class StudentSkillResponse(StudentSkillBase):
    id: str
    student_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Student Level Schemas =====
class StudentLevelBase(BaseModel):
    grade: str = Field(..., min_length=1, max_length=50)
    stream: Optional[str] = Field(None, max_length=50)
    overall_progress: Decimal = Field(default=0.0, ge=0, le=100)
    academic_year: Optional[str] = Field(None, max_length=20)


class StudentLevelCreate(StudentLevelBase):
    student_id: str


class StudentLevelUpdate(BaseModel):
    grade: Optional[str] = Field(None, min_length=1, max_length=50)
    stream: Optional[str] = Field(None, max_length=50)
    overall_progress: Optional[Decimal] = Field(None, ge=0, le=100)
    academic_year: Optional[str] = None


class StudentLevelResponse(StudentLevelBase):
    id: str
    student_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Subject Mark Schemas =====
class SubjectMarkBase(BaseModel):
    subject_name: str = Field(..., min_length=1, max_length=100)
    score: Decimal = Field(..., ge=0)
    max_score: Decimal = Field(default=100.0, ge=0)
    assessment_type: Optional[str] = Field(None, max_length=50)
    assessment_date: date
    course_id: Optional[str] = None

    @validator('score')
    def score_must_not_exceed_max(cls, v, values):
        if 'max_score' in values and v > values['max_score']:
            raise ValueError('score cannot exceed max_score')
        return v


class SubjectMarkCreate(SubjectMarkBase):
    student_id: str


class SubjectMarkUpdate(BaseModel):
    subject_name: Optional[str] = Field(None, min_length=1, max_length=100)
    score: Optional[Decimal] = Field(None, ge=0)
    max_score: Optional[Decimal] = Field(None, ge=0)
    assessment_type: Optional[str] = Field(None, max_length=50)
    assessment_date: Optional[date] = None
    course_id: Optional[str] = None


class SubjectMarkResponse(SubjectMarkBase):
    id: str
    student_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Improvement Area Schemas =====
class ImprovementAreaBase(BaseModel):
    subject_name: str = Field(..., min_length=1, max_length=100)
    reason: str = Field(..., min_length=1)
    suggestion: str = Field(..., min_length=1)
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    status: str = Field(default="active", pattern="^(active|in_progress|resolved)$")
    course_id: Optional[str] = None
    identified_date: date
    resolved_date: Optional[date] = None


class ImprovementAreaCreate(ImprovementAreaBase):
    student_id: str


class ImprovementAreaUpdate(BaseModel):
    subject_name: Optional[str] = Field(None, min_length=1, max_length=100)
    reason: Optional[str] = Field(None, min_length=1)
    suggestion: Optional[str] = Field(None, min_length=1)
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    status: Optional[str] = Field(None, pattern="^(active|in_progress|resolved)$")
    course_id: Optional[str] = None
    identified_date: Optional[date] = None
    resolved_date: Optional[date] = None


class ImprovementAreaResponse(ImprovementAreaBase):
    id: str
    student_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Dashboard Summary Schemas =====
class DashboardSummary(BaseModel):
    """Complete dashboard data for a student"""
    performance_trend: list[PerformanceTrendResponse]
    weekly_activity: list[WeeklyActivityResponse]
    skills: list[StudentSkillResponse]
    student_level: Optional[StudentLevelResponse]
    subject_marks: list[SubjectMarkResponse]
    improvement_areas: list[ImprovementAreaResponse]
