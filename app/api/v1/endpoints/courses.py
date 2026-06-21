from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, or_
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.course import Course, CourseEnrollment, CourseStatus, EnrollmentStatus
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseListResponse
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


# ===== Course CRUD Endpoints =====

@router.get("/student-courses", response_model=APIResponse)
async def get_student_courses(
    email: str = Query(..., description="Student's email address"),
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all courses for a specific student with progress tracking"""
    try:
        student = get_student_by_email(email, db)
        print(f"#################################################Fetching courses for student: {student.email} (ID: {student.id})")
        
        # Query enrollments with course and teacher info
        query = db.query(
            CourseEnrollment,
            Course,
            User.first_name,
            User.last_name,
            User.avatar.label('instructor_avatar')
        ).join(
            Course, CourseEnrollment.course_id == Course.id
        ).join(
            User, Course.teacher_id == User.id
        ).filter(
            CourseEnrollment.student_id == student.id
        )
        
        print("########### QUERY BUILT, applying filters... ###########")
        print(query)
        
        # Apply filters
        if status_filter:
            query = query.filter(CourseEnrollment.status == status_filter)
        
        if category:
            query = query.filter(Course.category == category)
        
        enrollments = query.all()
        
        # Build response
        courses = []
        for enrollment, course, first_name, last_name, instructor_avatar in enrollments:
            # Count total enrolled students
            enrolled_count = db.query(func.count(CourseEnrollment.id)).filter(
                CourseEnrollment.course_id == course.id,
                CourseEnrollment.status == EnrollmentStatus.ACTIVE
            ).scalar() or 0
            
            course_dict = {
                "id": str(course.id),
                "title": course.title,
                "description": course.description,
                "category": course.category,
                "level": course.level,
                "duration": course.duration,
                "thumbnail": course.thumbnail,
                "teacher_id": str(course.teacher_id),
                "instructor": f"{first_name} {last_name}",
                "instructor_avatar": instructor_avatar,
                "status": course.status,
                "enrolled": enrolled_count,
                "progress": float(enrollment.progress or 0),
                "enrollment_date": enrollment.enrollment_date,
                "created_at": course.created_at,
                "updated_at": course.updated_at
            }
            courses.append(course_dict)
        print("##############PRINITNG COURSES##############")
        print(courses)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(courses)} courses",
            data={
                "courses": courses,
                "count": len(courses)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving courses: {str(e)}"
        )


@router.get("/{course_id}", response_model=APIResponse)
async def get_course_detail(
    course_id: str,
    email: Optional[str] = Query(None, description="Student's email for progress tracking"),
    db: Session = Depends(get_db)
):
    """Get detailed course information"""
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        # Get teacher info
        teacher = db.query(User).filter(User.id == course.teacher_id).first()
        
        # Count enrolled students
        enrolled_count = db.query(func.count(CourseEnrollment.id)).filter(
            CourseEnrollment.course_id == course.id,
            CourseEnrollment.status == EnrollmentStatus.ACTIVE
        ).scalar() or 0
        
        # Get student progress if email provided
        progress = 0
        enrollment_date = None
        if email:
            student = get_student_by_email(email, db)
            enrollment = db.query(CourseEnrollment).filter(
                and_(
                    CourseEnrollment.student_id == student.id,
                    CourseEnrollment.course_id == course_id
                )
            ).first()
            
            if enrollment:
                progress = float(enrollment.progress or 0)
                enrollment_date = enrollment.enrollment_date
        
        course_dict = {
            "id": str(course.id),
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "level": course.level,
            "duration": course.duration,
            "thumbnail": course.thumbnail,
            "teacher_id": str(course.teacher_id),
            "instructor": teacher.full_name if teacher else None,
            "instructor_avatar": teacher.avatar if teacher else None,
            "status": course.status,
            "enrolled": enrolled_count,
            "progress": progress,
            "enrollment_date": enrollment_date,
            "created_at": course.created_at,
            "updated_at": course.updated_at
        }
        
        return APIResponse(
            success=True,
            message="Course retrieved successfully",
            data=course_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving course: {str(e)}"
        )


@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new course (Teacher only)"""
    try:
        if current_user.role != UserRole.TEACHER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can create courses"
            )
        
        course = Course(
            teacher_id=str(current_user.id),
            title=course_data.title,
            description=course_data.description,
            category=course_data.category,
            level=course_data.level,
            duration=course_data.duration,
            thumbnail=course_data.thumbnail,
            status=CourseStatus.ACTIVE  # Default to active
        )
        
        db.add(course)
        db.commit()
        db.refresh(course)
        
        course_dict = {
            "id": str(course.id),
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "level": course.level,
            "duration": course.duration,
            "thumbnail": course.thumbnail,
            "teacher_id": str(course.teacher_id),
            "instructor": current_user.full_name,
            "instructor_avatar": current_user.avatar,
            "status": course.status,
            "enrolled": 0,
            "progress": 0,
            "enrollment_date": None,
            "created_at": course.created_at,
            "updated_at": course.updated_at
        }
        
        return APIResponse(
            success=True,
            message="Course created successfully",
            data=course_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating course: {str(e)}"
        )


@router.put("/{course_id}", response_model=APIResponse)
async def update_course(
    course_id: str,
    course_data: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a course (Teacher only - must be course owner)"""
    try:
        if current_user.role != UserRole.TEACHER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can update courses"
            )
        
        course = db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        # Verify teacher owns the course
        if str(course.teacher_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own courses"
            )
        
        # Update fields
        update_data = course_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(course, key, value)
        
        db.commit()
        db.refresh(course)
        
        # Count enrolled students
        enrolled_count = db.query(func.count(CourseEnrollment.id)).filter(
            CourseEnrollment.course_id == course.id,
            CourseEnrollment.status == EnrollmentStatus.ACTIVE
        ).scalar() or 0
        
        course_dict = {
            "id": str(course.id),
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "level": course.level,
            "duration": course.duration,
            "thumbnail": course.thumbnail,
            "teacher_id": str(course.teacher_id),
            "instructor": current_user.full_name,
            "instructor_avatar": current_user.avatar,
            "status": course.status,
            "enrolled": enrolled_count,
            "progress": 0,
            "enrollment_date": None,
            "created_at": course.created_at,
            "updated_at": course.updated_at
        }
        
        return APIResponse(
            success=True,
            message="Course updated successfully",
            data=course_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating course: {str(e)}"
        )


@router.delete("/{course_id}", response_model=APIResponse)
async def delete_course(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a course (Teacher only - must be course owner)"""
    try:
        if current_user.role != UserRole.TEACHER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can delete courses"
            )
        
        course = db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        # Verify teacher owns the course
        if str(course.teacher_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own courses"
            )
        
        db.delete(course)
        db.commit()
        
        return APIResponse(
            success=True,
            message="Course deleted successfully",
            data=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting course: {str(e)}"
        )


@router.get("/", response_model=APIResponse)
async def get_all_courses(
    category: Optional[str] = None,
    level: Optional[str] = None,
    status_filter: Optional[str] = Query("active", alias="status"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all available courses (public endpoint)"""
    try:
        query = db.query(Course).join(User, Course.teacher_id == User.id)
        
        # Apply filters
        if status_filter:
            query = query.filter(Course.status == status_filter)
        
        if category:
            query = query.filter(Course.category == category)
        
        if level:
            query = query.filter(Course.level == level)
        
        courses_data = query.limit(limit).all()
        
        # Build response
        courses = []
        for course in courses_data:
            teacher = db.query(User).filter(User.id == course.teacher_id).first()
            
            # Count enrolled students
            enrolled_count = db.query(func.count(CourseEnrollment.id)).filter(
                CourseEnrollment.course_id == course.id,
                CourseEnrollment.status == EnrollmentStatus.ACTIVE
            ).scalar() or 0
            
            course_dict = {
                "id": str(course.id),
                "title": course.title,
                "description": course.description,
                "category": course.category,
                "level": course.level,
                "duration": course.duration,
                "thumbnail": course.thumbnail,
                "teacher_id": str(course.teacher_id),
                "instructor": teacher.full_name if teacher else None,
                "instructor_avatar": teacher.avatar if teacher else None,
                "status": course.status,
                "enrolled": enrolled_count,
                "progress": 0,
                "enrollment_date": None,
                "created_at": course.created_at,
                "updated_at": course.updated_at
            }
            courses.append(course_dict)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(courses)} courses",
            data={
                "courses": courses,
                "count": len(courses)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving courses: {str(e)}"
        )
