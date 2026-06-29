from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.security import get_password_hash
from app.schemas.common import APIResponse
from app.schemas.user import UserRegistration, AdminUserUpdate
from app.schemas.course import AdminCourseCreate, CourseUpdate
from app.models.user import User, UserRole, UserStatus
from app.models.course import Course, CourseEnrollment, CourseStatus
from app.models.grade import Grade
from app.models.system_health import SystemHealth
from app.models.activity_log import ActivityLog
from app.models.system_alert import SystemAlert
from app.repositories.user import UserRepository
from app.repositories.course import CourseRepository
from app.services.auth import AuthService

router = APIRouter()

# Dashboard endpoints
@router.get("/dashboard/stats", response_model=APIResponse)
async def get_admin_stats(
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics from database"""
    try:
        # Fetch system health data (latest record)
        latest_health = db.query(SystemHealth).order_by(
            SystemHealth.timestamp.desc()
        ).first()
        
        # Fetch activity logs for recent activities
        recent_activities_logs = db.query(ActivityLog).order_by(
            ActivityLog.timestamp.desc()
        ).limit(5).all()
        
        # Fetch system alerts
        system_alerts_data = db.query(SystemAlert).filter(
            SystemAlert.is_resolved == False
        ).order_by(SystemAlert.created_at.desc()).limit(10).all()
        
        # Get user distribution from existing data
        user_distribution = db.query(
            User.role, User.status, func.count(User.id).label('count')
        ).group_by(User.role, User.status).all()
        
        # Get courses info
        courses_query = db.query(
            Course.id,
            Course.title,
            func.count(func.distinct(CourseEnrollment.student_id)).label('student_count')
        ).outerjoin(CourseEnrollment, Course.id == CourseEnrollment.course_id).group_by(
            Course.id, Course.title
        ).limit(10).all()
        
        # Calculate change metrics from health records
        # Get previous health record (from 24 hours ago)
        yesterday_health = db.query(SystemHealth).filter(
            SystemHealth.timestamp <= datetime.now() - timedelta(days=1)
        ).order_by(SystemHealth.timestamp.desc()).first()
        
        total_users = db.query(func.count(User.id)).scalar() or 0
        active_courses = db.query(func.count(Course.id)).filter(
            Course.status == CourseStatus.ACTIVE
        ).scalar() or 0
        
        # Build stats with data from database
        current_health = latest_health.api_uptime if latest_health else 95
        previous_health = yesterday_health.api_uptime if yesterday_health else 93
        health_change = current_health - previous_health
        
        stats = {
            "total_users": total_users,
            "total_users_change": {"value": 5, "trend": "up"},
            "active_courses": active_courses,
            "active_courses_change": {"value": 2, "trend": "up"},
            "system_health": int(current_health),
            "system_health_change": {"value": int(abs(health_change)), "trend": "up" if health_change >= 0 else "down"},
            "pending_issues": len(system_alerts_data),
            "pending_issues_change": {"value": 0, "trend": "down"}
        }
        
        # Format user distribution
        user_dist = [
            {
                "role": str(row.role.value) if row.role else "unknown",
                "count": row.count,
                "status": str(row.status.value) if row.status else "unknown"
            }
            for row in user_distribution
        ]
        
        # Format recent activities from ActivityLog table
        recent_activities = [
            {
                "id": idx + 1,
                "user": log.user.full_name if log.user else "Unknown User",
                "action": log.action,
                "time": f"{(datetime.now() - log.timestamp).seconds // 3600} hours ago" if log.timestamp else "recently"
            }
            for idx, log in enumerate(recent_activities_logs)
        ]
        
        # Format courses
        courses = [
            {
                "id": idx + 1,
                "name": row.title,
                "students": row.student_count or 0,
                "completion": 65
            }
            for idx, row in enumerate(courses_query)
        ]
        
        # Format system alerts from SystemAlert table
        system_alerts = [
            {
                "id": idx + 1,
                "type": alert.alert_type,
                "message": alert.message,
                "severity": alert.severity
            }
            for idx, alert in enumerate(system_alerts_data)
        ]
        
        data = {
            "stats": stats,
            "user_distribution": user_dist,
            "recent_activities": recent_activities,
            "courses": courses,
            "system_alerts": system_alerts
        }
        
        return APIResponse(success=True, data=data, message="Dashboard stats retrieved successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# User management endpoints
@router.get("/users", response_model=APIResponse)
async def get_all_users(
    db: Session = Depends(get_db),
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    """Get all users with search, filters, and pagination"""
    try:
        repo = UserRepository(db)
        role_filter = UserRole(role) if role else None
        status_filter = UserStatus(status) if status else None
        users = repo.get_all(
            skip=(page-1)*limit, limit=limit,
            role=role_filter, status=status_filter, search=search
        )
        total = repo.count(role=role_filter, status=status_filter, search=search)
        
        users_data = [
            {
                "id": u.id,
                "email": u.email,
                "firstName": u.first_name,
                "lastName": u.last_name,
                "role": u.role.value,
                "status": u.status.value,
                "phone": u.phone,
                "avatar": u.avatar,
                "lastLogin": u.last_login.isoformat() if u.last_login else None,
                "emailVerified": u.email_verified,
                "createdAt": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
        return APIResponse(success=True, data={
            "users": users_data,
            "pagination": {
                "page": page, "limit": limit,
                "total": total,
                "totalPages": (total + limit - 1) // limit if total > 0 else 0
            }
        }, message="Users retrieved successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users", response_model=APIResponse)
async def create_user(
    user_data: UserRegistration,
    db: Session = Depends(get_db)
):
    """Create a new user (admin)"""
    try:
        auth_service = AuthService(db)
        result = auth_service.register_user(user_data)
        return APIResponse(success=True, data=result, message="User created successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/users/{user_id}", response_model=APIResponse)
async def update_user(
    user_id: str,
    update_data: AdminUserUpdate,
    db: Session = Depends(get_db)
):
    """Update user details, role, or status"""
    try:
        repo = UserRepository(db)
        user = repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        update_dict = update_data.dict(exclude_none=True)
        if "password" in update_dict:
            update_dict["password_hash"] = get_password_hash(update_dict.pop("password"))
        
        updated_user = repo.update(user_id, update_dict)
        return APIResponse(success=True, data={
            "id": updated_user.id,
            "email": updated_user.email,
            "firstName": updated_user.first_name,
            "lastName": updated_user.last_name,
            "role": updated_user.role.value,
            "status": updated_user.status.value,
        }, message="User updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}", response_model=APIResponse)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Delete a user"""
    try:
        repo = UserRepository(db)
        deleted = repo.delete(user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")
        return APIResponse(success=True, message="User deleted successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{user_id}/status", response_model=APIResponse)
async def update_user_status(
    user_id: str,
    status_data: dict,
    db: Session = Depends(get_db)
):
    """Update user status (activate/deactivate/suspend)"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if "status" in status_data:
            user.status = UserStatus(status_data["status"])
            db.commit()
        
        return APIResponse(success=True, message=f"User {user_id} status updated to {status_data.get('status', 'unknown')}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# System management endpoints
@router.get("/system/info", response_model=APIResponse)
async def get_system_info(
    db: Session = Depends(get_db)
):
    """Get system information and health status"""
    try:
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_courses = db.query(func.count(Course.id)).scalar() or 0
        active_courses = db.query(func.count(Course.id)).filter(
            Course.status == CourseStatus.ACTIVE
        ).scalar() or 0
        
        system_info = {
            "version": "1.0.0",
            "databaseStatus": "Connected",
            "uptime": "5 days",
            "totalStorage": "100GB",
            "usedStorage": "25GB",
            "totalUsers": total_users,
            "totalCourses": total_courses,
            "activeCourses": active_courses
        }
        return APIResponse(success=True, data=system_info, message="System info retrieved successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Courses endpoints
@router.get("/courses", response_model=APIResponse)
async def get_courses(
    db: Session = Depends(get_db)
):
    """Get all courses with details"""
    try:
        courses_query = db.query(
            Course.id,
            Course.title,
            Course.code,
            Course.instructor,
            Course.status,
            Course.created_at,
            Course.updated_at,
            User.first_name,
            User.last_name,
            func.count(func.distinct(CourseEnrollment.student_id)).label('student_count')
        ).outerjoin(User, Course.teacher_id == User.id).outerjoin(
            CourseEnrollment, Course.id == CourseEnrollment.course_id
        ).group_by(
            Course.id, Course.title, Course.code, Course.instructor, 
            Course.status, Course.created_at, Course.updated_at,
            User.first_name, User.last_name
        ).all()
        
        courses = [
            {
                "id": str(row.id),
                "title": row.title,
                "code": row.code or "N/A",
                "instructor": row.instructor or f"{row.first_name} {row.last_name}".strip() or "Unassigned",
                "students": row.student_count or 0,
                "status": str(row.status.value) if row.status else "draft",
                "startDate": row.created_at.strftime("%Y-%m-%d") if row.created_at else "",
                "endDate": row.updated_at.strftime("%Y-%m-%d") if row.updated_at else ""
            }
            for row in courses_query
        ]
        
        return APIResponse(success=True, data={"courses": courses}, message="Courses retrieved successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/courses", response_model=APIResponse)
async def create_course(
    course_data: AdminCourseCreate,
    db: Session = Depends(get_db)
):
    """Create a new course (admin)"""
    try:
        repo = CourseRepository(db)
        course = repo.create(course_data.dict())
        return APIResponse(success=True, data={
            "id": str(course.id),
            "title": course.title,
            "code": course.code,
            "instructor": course.instructor,
            "teacher_id": str(course.teacher_id),
            "status": course.status.value,
        }, message="Course created successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/courses/{course_id}", response_model=APIResponse)
async def update_course(
    course_id: str,
    course_data: CourseUpdate,
    db: Session = Depends(get_db)
):
    """Update a course (admin)"""
    try:
        repo = CourseRepository(db)
        course = repo.update(course_id, course_data.dict(exclude_none=True))
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return APIResponse(success=True, data={
            "id": str(course.id),
            "title": course.title,
            "code": course.code,
            "instructor": course.instructor,
            "teacher_id": str(course.teacher_id),
            "status": course.status.value,
        }, message="Course updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/courses/{course_id}", response_model=APIResponse)
async def delete_course(
    course_id: str,
    db: Session = Depends(get_db)
):
    """Delete a course (admin)"""
    try:
        repo = CourseRepository(db)
        deleted = repo.delete(course_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Course not found")
        return APIResponse(success=True, message="Course deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teachers", response_model=APIResponse)
async def get_teachers(
    db: Session = Depends(get_db)
):
    """Get all teachers for course assignment"""
    try:
        repo = UserRepository(db)
        teachers = repo.get_teachers(limit=500)
        teachers_data = [
            {
                "id": t.id,
                "firstName": t.first_name,
                "lastName": t.last_name,
                "email": t.email,
            }
            for t in teachers
        ]
        return APIResponse(success=True, data={"teachers": teachers_data}, message="Teachers retrieved successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/students", response_model=APIResponse)
async def get_students(
    db: Session = Depends(get_db)
):
    """Get all students for enrollment"""
    try:
        repo = UserRepository(db)
        students = repo.get_students(limit=500)
        students_data = [
            {
                "id": s.id,
                "firstName": s.first_name,
                "lastName": s.last_name,
                "email": s.email,
            }
            for s in students
        ]
        return APIResponse(success=True, data={"students": students_data}, message="Students retrieved successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/courses/{course_id}/enrollments", response_model=APIResponse)
async def get_course_enrollments(
    course_id: str,
    db: Session = Depends(get_db)
):
    """Get all enrollments for a course"""
    try:
        repo = CourseRepository(db)
        enrollments = repo.get_course_enrollments(course_id)
        enrollments_data = [
            {
                "studentId": str(e.student_id),
                "firstName": e.student.first_name if e.student else "",
                "lastName": e.student.last_name if e.student else "",
                "email": e.student.email if e.student else "",
                "enrolledAt": e.enrollment_date.isoformat() if e.enrollment_date else None,
                "status": e.status.value,
                "progress": float(e.progress or 0),
            }
            for e in enrollments if e.status.value != "dropped"
        ]
        return APIResponse(
            success=True,
            data={"enrollments": enrollments_data},
            message="Enrollments retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/courses/{course_id}/enroll", response_model=APIResponse)
async def enroll_student(
    course_id: str,
    body: dict,
    db: Session = Depends(get_db)
):
    """Enroll a student in a course"""
    try:
        student_id = body.get("student_id")
        if not student_id:
            raise HTTPException(status_code=400, detail="student_id is required")

        repo = CourseRepository(db)
        existing = repo.get_enrollment(course_id, student_id)
        if existing:
            if existing.status.value == "dropped":
                existing.status = "active"
                db.commit()
                db.refresh(existing)
                return APIResponse(success=True, message="Student re-enrolled successfully")
            raise HTTPException(status_code=409, detail="Student is already enrolled in this course")

        enrollment = repo.enroll_student(course_id, student_id)
        return APIResponse(success=True, data={
            "enrollmentId": str(enrollment.id),
            "studentId": str(enrollment.student_id),
        }, message="Student enrolled successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/courses/{course_id}/enroll/{student_id}", response_model=APIResponse)
async def unenroll_student(
    course_id: str,
    student_id: str,
    db: Session = Depends(get_db)
):
    """Unenroll a student from a course (soft-delete)"""
    try:
        repo = CourseRepository(db)
        enrollment = repo.unenroll_student(course_id, student_id)
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        return APIResponse(success=True, message="Student unenrolled successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))