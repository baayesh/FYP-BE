from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import Optional, List
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.student_performance import (
    PerformanceTrend,
    WeeklyActivity,
    StudentSkill,
    StudentLevel,
    SubjectMark,
    ImprovementArea
)
from app.schemas.student_performance import (
    PerformanceTrendCreate,
    PerformanceTrendUpdate,
    PerformanceTrendResponse,
    WeeklyActivityCreate,
    WeeklyActivityUpdate,
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


def get_student_by_email(email: str, db: Session) -> User:
    """Get student user by email and validate role"""
    user = db.query(User).filter(
        and_(User.email == email, User.role == UserRole.STUDENT)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found with the provided email"
        )
    
    if user.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student account is not active"
        )
    
    return user


# ===== Complete Dashboard Summary =====
@router.get("/dashboard", response_model=APIResponse)
async def get_complete_dashboard(
    email: str = Query(..., description="Student's email address"),
    days: int = Query(30, ge=1, le=365, description="Number of days for performance trend"),
    db: Session = Depends(get_db)
):
    """
    Get complete dashboard data for a student including:
    - Performance trend
    - Weekly activity
    - Skills assessment
    - Student level
    - Subject marks
    - Improvement areas
    """
    try:
        student = get_student_by_email(email, db)
        student_id = student.id
        cutoff_date = date.today() - timedelta(days=days)
        print(f"Fetching dashboard data for student_id={student_id} with cutoff_date={cutoff_date}")
        
        # Get performance trend
        performance = db.query(PerformanceTrend).filter(
            PerformanceTrend.student_id == student_id,
            PerformanceTrend.date >= cutoff_date
        ).order_by(PerformanceTrend.date).all()
        
        # Get weekly activity (last 7 days)
        week_ago = date.today() - timedelta(days=7)
        activity = db.query(WeeklyActivity).filter(
            WeeklyActivity.student_id == student_id,
            WeeklyActivity.date >= week_ago
        ).order_by(WeeklyActivity.date).all()
        
        # Get skills
        skills = db.query(StudentSkill).filter(
            StudentSkill.student_id == student_id
        ).all()
        
        # Get student level
        level = db.query(StudentLevel).filter(
            StudentLevel.student_id == student_id
        ).first()
        
        # Get subject marks (latest for each subject)
        # Subquery approach for SQLite compatibility (DISTINCT ON is PG-only)
        latest_subquery = db.query(
            SubjectMark.subject_name,
            func.max(SubjectMark.assessment_date).label('max_date')
        ).filter(
            SubjectMark.student_id == student_id
        ).group_by(SubjectMark.subject_name).subquery()

        marks = db.query(SubjectMark).filter(
            SubjectMark.student_id == student_id,
            and_(
                SubjectMark.subject_name == latest_subquery.c.subject_name,
                SubjectMark.assessment_date == latest_subquery.c.max_date
            )
        ).order_by(SubjectMark.subject_name).all()
        
        # Get active improvement areas
        improvements = db.query(ImprovementArea).filter(
            ImprovementArea.student_id == student_id,
            ImprovementArea.status == "active"
        ).order_by(
            ImprovementArea.priority.desc(),
            ImprovementArea.identified_date
        ).all()
        
        dashboard_data = DashboardSummary(
            performance_trend=[PerformanceTrendResponse.model_validate(p) for p in performance],
            weekly_activity=[WeeklyActivityResponse.model_validate(a) for a in activity],
            skills=[StudentSkillResponse.model_validate(s) for s in skills],
            student_level=StudentLevelResponse.model_validate(level) if level else None,
            subject_marks=[SubjectMarkResponse.model_validate(m) for m in marks],
            improvement_areas=[ImprovementAreaResponse.model_validate(i) for i in improvements]
        )
        
        return APIResponse(
            success=True,
            message="Dashboard data retrieved successfully",
            data=dashboard_data.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving dashboard data: {str(e)}"
        )


# ===== Performance Trend Endpoints =====
@router.get("/performance-trend", response_model=APIResponse)
async def get_performance_trend(
    email: str = Query(..., description="Student's email address"),
    days: int = Query(30, ge=1, le=365),
    course_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get student's performance trend over time"""
    try:
        student = get_student_by_email(email, db)
        cutoff_date = date.today() - timedelta(days=days)
        query = db.query(PerformanceTrend).filter(
            PerformanceTrend.student_id == student.id,
            PerformanceTrend.date >= cutoff_date
        )
        
        if course_id:
            query = query.filter(PerformanceTrend.course_id == course_id)
        
        trends = query.order_by(PerformanceTrend.date).all()

        # Wrap list in a dict to satisfy APIResponse.data schema (expects a dict)
        return APIResponse(
            success=True,
            message=f"Retrieved {len(trends)} performance records",
            data={
                "performance_trend": [
                    PerformanceTrendResponse.model_validate(t) for t in trends
                ],
                "count": len(trends)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/performance-trend", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_performance_trend(
    trend_data: PerformanceTrendCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new performance trend record (Admin/Teacher only)"""
    try:
        if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and teachers can create performance records"
            )
        
        trend = PerformanceTrend(**trend_data.dict())
        db.add(trend)
        db.commit()
        db.refresh(trend)
        
        return APIResponse(
            success=True,
            message="Performance trend created successfully",
            data=PerformanceTrendResponse.model_validate(trend)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ===== Weekly Activity Endpoints =====
@router.get("/weekly-activity", response_model=APIResponse)
async def get_weekly_activity(
    email: str = Query(..., description="Student's email address"),
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get student's weekly activity data"""
    try:
        student = get_student_by_email(email, db)
        cutoff_date = date.today() - timedelta(days=days)
        activities = db.query(WeeklyActivity).filter(
            WeeklyActivity.student_id == student.id,
            WeeklyActivity.date >= cutoff_date
        ).order_by(WeeklyActivity.date).all()
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(activities)} activity records",
            data=[WeeklyActivityResponse.model_validate(a) for a in activities]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/weekly-activity", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_weekly_activity(
    activity_data: WeeklyActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create weekly activity record (Admin/System only)"""
    try:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create activity records"
            )
        
        activity = WeeklyActivity(**activity_data.dict())
        db.add(activity)
        db.commit()
        db.refresh(activity)
        
        return APIResponse(
            success=True,
            message="Weekly activity created successfully",
            data=WeeklyActivityResponse.model_validate(activity)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ===== Student Skills Endpoints =====
@router.get("/skills", response_model=APIResponse)
async def get_student_skills(
    email: str = Query(..., description="Student's email address"),
    course_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get student's skill assessments"""
    try:
        student = get_student_by_email(email, db)
        query = db.query(StudentSkill).filter(
            StudentSkill.student_id == student.id
        )
        
        if course_id:
            query = query.filter(StudentSkill.course_id == course_id)
        
        skills = query.all()
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(skills)} skill assessments",
            data=[StudentSkillResponse.model_validate(s) for s in skills]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/skills", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_skill_assessment(
    skill_data: StudentSkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create skill assessment (Admin/Teacher only)"""
    try:
        if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and teachers can create skill assessments"
            )
        
        skill = StudentSkill(**skill_data.dict())
        db.add(skill)
        db.commit()
        db.refresh(skill)
        
        return APIResponse(
            success=True,
            message="Skill assessment created successfully",
            data=StudentSkillResponse.model_validate(skill)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/skills/{skill_id}", response_model=APIResponse)
async def update_skill_assessment(
    skill_id: str,
    skill_data: StudentSkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update skill assessment (Admin/Teacher only)"""
    try:
        if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and teachers can update skill assessments"
            )
        
        skill = db.query(StudentSkill).filter(StudentSkill.id == skill_id).first()
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill assessment not found"
            )
        
        for key, value in skill_data.dict(exclude_unset=True).items():
            setattr(skill, key, value)
        
        db.commit()
        db.refresh(skill)
        
        return APIResponse(
            success=True,
            message="Skill assessment updated successfully",
            data=StudentSkillResponse.model_validate(skill)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ===== Student Level Endpoints =====
@router.get("/level", response_model=APIResponse)
async def get_student_level(
    email: str = Query(..., description="Student's email address"),
    db: Session = Depends(get_db)
):
    """Get student's current academic level"""
    try:
        student = get_student_by_email(email, db)
        level = db.query(StudentLevel).filter(
            StudentLevel.student_id == student.id
        ).first()
        
        if not level:
            return APIResponse(
                success=True,
                message="No level information found",
                data=None
            )
        
        return APIResponse(
            success=True,
            message="Student level retrieved successfully",
            data=StudentLevelResponse.model_validate(level)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/level", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_student_level(
    level_data: StudentLevelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create student level (Admin only)"""
    try:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create student levels"
            )
        
        # Check if level already exists
        existing = db.query(StudentLevel).filter(
            StudentLevel.student_id == level_data.student_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student level already exists. Use PUT to update."
            )
        
        level = StudentLevel(**level_data.dict())
        db.add(level)
        db.commit()
        db.refresh(level)
        
        return APIResponse(
            success=True,
            message="Student level created successfully",
            data=StudentLevelResponse.model_validate(level)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/level", response_model=APIResponse)
async def update_student_level(
    level_data: StudentLevelUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update student level (Admin only)"""
    try:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update student levels"
            )
        
        level = db.query(StudentLevel).filter(
            StudentLevel.student_id == current_user.id
        ).first()
        
        if not level:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student level not found. Use POST to create."
            )
        
        for key, value in level_data.dict(exclude_unset=True).items():
            setattr(level, key, value)
        
        db.commit()
        db.refresh(level)
        
        return APIResponse(
            success=True,
            message="Student level updated successfully",
            data=StudentLevelResponse.model_validate(level)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
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
    try:
        student = get_student_by_email(email, db)
        cutoff_date = date.today() - timedelta(days=days)
        query = db.query(SubjectMark).filter(
            SubjectMark.student_id == student.id,
            SubjectMark.assessment_date >= cutoff_date
        )
        
        if subject_name:
            query = query.filter(SubjectMark.subject_name == subject_name)
        
        if assessment_type:
            query = query.filter(SubjectMark.assessment_type == assessment_type)
        
        marks = query.order_by(desc(SubjectMark.assessment_date)).all()
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(marks)} subject marks",
            data=[SubjectMarkResponse.model_validate(m) for m in marks]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/subject-marks", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_subject_mark(
    mark_data: SubjectMarkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create subject mark (Admin/Teacher only)"""
    try:
        if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and teachers can create subject marks"
            )
        
        mark = SubjectMark(**mark_data.dict())
        db.add(mark)
        db.commit()
        db.refresh(mark)
        
        return APIResponse(
            success=True,
            message="Subject mark created successfully",
            data=SubjectMarkResponse.model_validate(mark)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
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
    try:
        student = get_student_by_email(email, db)
        query = db.query(ImprovementArea).filter(
            ImprovementArea.student_id == student.id
        )
        
        if status_filter:
            query = query.filter(ImprovementArea.status == status_filter)
        
        if priority:
            query = query.filter(ImprovementArea.priority == priority)
        
        improvements = query.order_by(
            ImprovementArea.priority.desc(),
            ImprovementArea.identified_date
        ).all()
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(improvements)} improvement areas",
            data=[ImprovementAreaResponse.model_validate(i) for i in improvements]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/improvement-areas", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_improvement_area(
    improvement_data: ImprovementAreaCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create improvement area (Admin/Teacher only)"""
    try:
        if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and teachers can create improvement areas"
            )
        
        improvement = ImprovementArea(**improvement_data.dict())
        db.add(improvement)
        db.commit()
        db.refresh(improvement)
        
        return APIResponse(
            success=True,
            message="Improvement area created successfully",
            data=ImprovementAreaResponse.model_validate(improvement)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/improvement-areas/{improvement_id}", response_model=APIResponse)
async def update_improvement_area(
    improvement_id: str,
    improvement_data: ImprovementAreaUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update improvement area (Admin/Teacher only)"""
    try:
        if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and teachers can update improvement areas"
            )
        
        improvement = db.query(ImprovementArea).filter(
            ImprovementArea.id == improvement_id
        ).first()
        
        if not improvement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Improvement area not found"
            )
        
        for key, value in improvement_data.dict(exclude_unset=True).items():
            setattr(improvement, key, value)
        
        db.commit()
        db.refresh(improvement)
        
        return APIResponse(
            success=True,
            message="Improvement area updated successfully",
            data=ImprovementAreaResponse.model_validate(improvement)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/improvement-areas/{improvement_id}", response_model=APIResponse)
async def delete_improvement_area(
    improvement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete improvement area (Admin only)"""
    try:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can delete improvement areas"
            )
        
        improvement = db.query(ImprovementArea).filter(
            ImprovementArea.id == improvement_id
        ).first()
        
        if not improvement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Improvement area not found"
            )
        
        db.delete(improvement)
        db.commit()
        
        return APIResponse(
            success=True,
            message="Improvement area deleted successfully",
            data=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ===== Analytics Endpoints =====
@router.get("/analytics/summary", response_model=APIResponse)
async def get_analytics_summary(
    email: str = Query(..., description="Student's email address"),
    db: Session = Depends(get_db)
):
    """Get analytics summary for student"""
    try:
        student = get_student_by_email(email, db)
        student_id = student.id
        
        # Average performance score (last 30 days)
        thirty_days_ago = date.today() - timedelta(days=30)
        avg_performance = db.query(func.avg(PerformanceTrend.score)).filter(
            PerformanceTrend.student_id == student_id,
            PerformanceTrend.date >= thirty_days_ago
        ).scalar() or 0
        
        # Total study hours (last 7 days)
        week_ago = date.today() - timedelta(days=7)
        total_hours = db.query(func.sum(WeeklyActivity.hours_studied)).filter(
            WeeklyActivity.student_id == student_id,
            WeeklyActivity.date >= week_ago
        ).scalar() or 0
        
        # Total assignments completed (last 7 days)
        total_assignments = db.query(func.sum(WeeklyActivity.assignments_completed)).filter(
            WeeklyActivity.student_id == student_id,
            WeeklyActivity.date >= week_ago
        ).scalar() or 0
        
        # Average skill level
        avg_skill = db.query(func.avg(StudentSkill.skill_value)).filter(
            StudentSkill.student_id == student_id
        ).scalar() or 0
        
        # Active improvement areas count
        active_improvements = db.query(func.count(ImprovementArea.id)).filter(
            ImprovementArea.student_id == student_id,
            ImprovementArea.status == "active"
        ).scalar() or 0
        
        summary = {
            "average_performance": float(avg_performance),
            "total_study_hours_week": float(total_hours),
            "total_assignments_week": int(total_assignments),
            "average_skill_level": float(avg_skill),
            "active_improvement_areas": int(active_improvements)
        }
        
        return APIResponse(
            success=True,
            message="Analytics summary retrieved successfully",
            data=summary
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
