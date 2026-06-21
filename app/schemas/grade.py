from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class GradeItemResponse(BaseModel):
    id: str
    subject: str
    item_type: str
    item_name: str
    score: Optional[float] = None
    max_score: Optional[float] = None
    percentage: float
    letter_grade: Optional[str] = None
    date: Optional[str] = None
    feedback: Optional[str] = None

    class Config:
        from_attributes = True


class SubjectSummaryResponse(BaseModel):
    subject: str
    average: float
    grade: str
    trend: str


class StudentGradesResponse(BaseModel):
    grades: list[GradeItemResponse]
    subject_summaries: list[SubjectSummaryResponse]
    overall_average: float
