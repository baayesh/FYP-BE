from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_admin_user, get_teacher_or_admin
from app.services.performance_service import PerformanceService
from app.models.user import User
from app.schemas.student_performance import (
    PerformanceTrendCreate,
    PerformanceTrendResponse,
    WeeklyActivityCreate,
    WeeklyActivityResponse,
    StudentSkillCreate,
    StudentSkillUpdate,
    StudentSkillResponse,
    StudentLevelCreate,
    StudentLevelUpdate,
    StudentLevelResponse,
    SubjectMarkCreate,
    SubjectMarkUpdate,
    SubjectMarkResponse,
    ImprovementAreaCreate,
    ImprovementAreaUpdate,
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
    service = PerformanceService(db)
    student = service.get_student_by_email(email)
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


# ===== Performance Trend Endpoints =====
@router.get("/performance-trend", response_model=APIResponse)
async def get_performance_trend(
    email: str = Query(..., description="Student's email address"),
    days: int = Query(30, ge=1, le=365),
    course_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get student's performance trend over time"""
    service = PerformanceService(db)
    student = service.get_student_by_email(email)
    trends = service.get_performance_trends(str(student.id), days, course_id)

    return APIResponse(
        success=True,
        message=f"Retrieved {len(trends)} performance records",
        data={
            "performance_trend": [PerformanceTrendResponse.model_validate(t) for t in trends],
            "count": len(trends)
        }
    )


@router.post("/performance-trend", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_performance_trend(
    trend_data: PerformanceTrendCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_admin)
):
    """Create a new performance trend record (Admin/Teacher only)"""
    service = PerformanceService(db)
    trend = service.create_performance_trend(trend_data.dict())
    return APIResponse(
        success=True,
        message="Performance trend created successfully",
        data=PerformanceTrendResponse.model_validate(trend)
    )


# ===== Weekly Activity Endpoints =====
@router.get("/weekly-activity", response_model=APIResponse)
async def get_weekly_activity(
    email: str = Query(..., description="Student's email address"),
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get student's weekly activity data"""
    service = PerformanceService(db)
    student = service.get_student_by_email(email)
    activities = service.get_weekly_activities(str(student.id), days)

    return APIResponse(
        success=True,
        message=f"Retrieved {len(activities)} activity records",
        data=[WeeklyActivityResponse.model_validate(a) for a in activities]
    )


@router.post("/weekly-activity", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_weekly_activity(
    activity_data: WeeklyActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Create weekly activity record (Admin only)"""
    service = PerformanceService(db)
    activity = service.create_weekly_activity(activity_data.dict())
    return APIResponse(
        success=True,
        message="Weekly activity created successfully",
        data=WeeklyActivityResponse.model_validate(activity)
    )


# ===== Student Skills Endpoints =====
@router.get("/skills", response_model=APIResponse)
async def get_student_skills(
    email: str = Query(..., description="Student's email address"),
    course_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get student's skill assessments"""
    service = PerformanceService(db)
    student = service.get_student_by_email(email)
    skills = service.get_skills(str(student.id), course_id)

    return APIResponse(
        success=True,
        message=f"Retrieved {len(skills)} skill assessments",
        data=[StudentSkillResponse.model_validate(s) for s in skills]
    )


@router.post("/skills", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_skill_assessment(
    skill_data: StudentSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_admin)
):
    """Create skill assessment (Admin/Teacher only)"""
    service = PerformanceService(db)
    skill = service.create_skill(skill_data.dict())
    return APIResponse(
        success=True,
        message="Skill assessment created successfully",
        data=StudentSkillResponse.model_validate(skill)
    )


@router.put("/skills/{skill_id}", response_model=APIResponse)
async def update_skill_assessment(
    skill_id: str,
    skill_data: StudentSkillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_admin)
):
    """Update skill assessment (Admin/Teacher only)"""
    service = PerformanceService(db)
    skill = service.update_skill(skill_id, skill_data.dict(exclude_unset=True))
    return APIResponse(
        success=True,
        message="Skill assessment updated successfully",
        data=StudentSkillResponse.model_validate(skill)
    )


# ===== Student Level Endpoints =====
@router.get("/level", response_model=APIResponse)
async def get_student_level(
    email: str = Query(..., description="Student's email address"),
    db: Session = Depends(get_db)
):
    """Get student's current academic level"""
    service = PerformanceService(db)
    student = service.get_student_by_email(email)
    level = service.get_level(str(student.id))

    if not level:
        return APIResponse(success=True, message="No level information found", data=None)

    return APIResponse(
        success=True,
        message="Student level retrieved successfully",
        data=StudentLevelResponse.model_validate(level)
    )


@router.post("/level", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_student_level(
    level_data: StudentLevelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Create student level (Admin only)"""
    service = PerformanceService(db)
    level = service.create_level(level_data.dict())
    return APIResponse(
        success=True,
        message="Student level created successfully",
        data=StudentLevelResponse.model_validate(level)
    )


@router.put("/level", response_model=APIResponse)
async def update_student_level(
    level_data: StudentLevelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Update student level (Admin only)"""
    service = PerformanceService(db)
    level = service.update_level(strcurrent_user.id, level_data.dict(exclude_unset=True))
    return APIResponse(
        success=True,
        message="Student level updated successfully",
        data=StudentLevelResponse.model_validate(level)
    )


# ===== Subject Marks Endpoints =====
@router.get("/subject-marks", response_model=APIResponse)
async def get_subject_marks(
    email: str = Query(..., description="Student's email address"),
    subject_name: Optional[str] = None,
    assessment_type: Optional[str] = None,
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get student's subject marks"""
    service = PerformanceService(db)
    student = service.get_student_by_email(email)
    marks = service.get_subject_marks(str(student.id), subject_name, assessment_type, days)

    return APIResponse(
        success=True,
        message=f"Retrieved {len(marks)} subject marks",
        data=[SubjectMarkResponse.model_validate(m) for m in marks]
    )


@router.post("/subject-marks", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_subject_mark(
    mark_data: SubjectMarkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_admin)
):
    """Create subject mark (Admin/Teacher only)"""
    service = PerformanceService(db)
    mark = service.create_subject_mark(mark_data.dict())
    return APIResponse(
        success=True,
        message="Subject mark created successfully",
        data=SubjectMarkResponse.model_validate(mark)
    )


# ===== Improvement Areas Endpoints =====
@router.get("/improvement-areas", response_model=APIResponse)
async def get_improvement_areas(
    email: str = Query(..., description="Student's email address"),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get student's improvement areas"""
    service = PerformanceService(db)
    student = service.get_student_by_email(email)
    improvements = service.get_improvement_areas(str(student.id), status_filter, priority)

    return APIResponse(
        success=True,
        message=f"Retrieved {len(improvements)} improvement areas",
        data=[ImprovementAreaResponse.model_validate(i) for i in improvements]
    )


@router.post("/improvement-areas", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_improvement_area(
    improvement_data: ImprovementAreaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_admin)
):
    """Create improvement area (Admin/Teacher only)"""
    service = PerformanceService(db)
    improvement = service.create_improvement_area(improvement_data.dict())
    return APIResponse(
        success=True,
        message="Improvement area created successfully",
        data=ImprovementAreaResponse.model_validate(improvement)
    )


@router.put("/improvement-areas/{improvement_id}", response_model=APIResponse)
async def update_improvement_area(
    improvement_id: str,
    improvement_data: ImprovementAreaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_admin)
):
    """Update improvement area (Admin/Teacher only)"""
    service = PerformanceService(db)
    improvement = service.update_improvement_area(improvement_id, improvement_data.dict(exclude_unset=True))
    return APIResponse(
        success=True,
        message="Improvement area updated successfully",
        data=ImprovementAreaResponse.model_validate(improvement)
    )


@router.delete("/improvement-areas/{improvement_id}", response_model=APIResponse)
async def delete_improvement_area(
    improvement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Delete improvement area (Admin only)"""
    service = PerformanceService(db)
    service.delete_improvement_area(improvement_id)
    return APIResponse(
        success=True,
        message="Improvement area deleted successfully",
        data=None
    )


# ===== Analytics Endpoints =====
@router.get("/analytics/summary", response_model=APIResponse)
async def get_analytics_summary(
    email: str = Query(..., description="Student's email address"),
    db: Session = Depends(get_db)
):
    """Get analytics summary for student"""
    service = PerformanceService(db)
    student = service.get_student_by_email(email)
    summary = service.get_analytics_summary(str(student.id))

    return APIResponse(
        success=True,
        message="Analytics summary retrieved successfully",
        data=summary
    )
