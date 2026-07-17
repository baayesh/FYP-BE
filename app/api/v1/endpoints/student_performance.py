from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.performance_service import PerformanceService
from app.services.student import StudentService
from app.schemas.student_performance import (
    PerformanceTrendResponse,
    WeeklyActivityResponse,
    StudentSkillResponse,
    StudentLevelResponse,
    SubjectMarkResponse,
    ImprovementAreaResponse,
    DashboardSummary
)
from app.schemas.common import APIResponse

router = APIRouter()


# ===== Complete Dashboard Summary =====
@router.get("/dashboard", response_model=APIResponse)
async def get_complete_dashboard(
    email: str = Query(..., description="Student's email address"),
    days: int = Query(30, ge=1, le=365, description="Number of days for performance trend"),
    db: Session = Depends(get_db)
):
    """Get complete dashboard data for a student including performance trend,
    weekly activity, skills assessment, student level, subject marks, and improvement areas."""
    student = StudentService(db).get_student_by_email(email)
    service = PerformanceService(db)
    data = service.get_complete_dashboard_data(str(student.id), days)

    dashboard = DashboardSummary(
        performance_trend=[PerformanceTrendResponse.model_validate(p) for p in data["performance_trend"]],
        weekly_activity=[WeeklyActivityResponse.model_validate(a) for a in data["weekly_activity"]],
        skills=[StudentSkillResponse.model_validate(s) for s in data["skills"]],
        student_level=StudentLevelResponse.model_validate(data["student_level"]) if data["student_level"] else None,
        subject_marks=[SubjectMarkResponse.model_validate(m) for m in data["subject_marks"]],
        improvement_areas=[ImprovementAreaResponse.model_validate(i) for i in data["improvement_areas"]]
    )
    return APIResponse(success=True, message="Dashboard data retrieved successfully", data=dashboard.dict())

