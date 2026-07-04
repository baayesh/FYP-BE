from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User, UserRole
from app.schemas.course import CourseCreate, CourseUpdate
from app.schemas.common import APIResponse
from app.services.course import CourseService

router = APIRouter()


@router.get("/student-courses", response_model=APIResponse)
async def get_student_courses(
    email: str = Query(..., description="Student's email address"),
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all courses for a specific student with progress tracking"""
    try:
        service = CourseService(db)
        result = service.get_student_courses(email, status_filter, category)
        print('########### STUDENT COURSES RESULT ###########')
        print(result)
        return APIResponse(
            success=True,
            message=f"Retrieved {result['count']} courses",
            data=result
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
        service = CourseService(db)
        course = service.get_course_detail(course_id, email)
        return APIResponse(
            success=True,
            message="Course retrieved successfully",
            data=course
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
        service = CourseService(db)
        course = service.create_course(str(current_user.id), course_data.dict())
        return APIResponse(
            success=True,
            message="Course created successfully",
            data=course
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
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
        service = CourseService(db)
        course = service.update_course(
            str(current_user.id),
            course_id,
            course_data.dict(exclude_unset=True)
        )
        return APIResponse(
            success=True,
            message="Course updated successfully",
            data=course
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
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
        service = CourseService(db)
        service.delete_course(str(current_user.id), course_id)
        return APIResponse(
            success=True,
            message="Course deleted successfully",
            data=None
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
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
        service = CourseService(db)
        result = service.get_all_courses(category, level, status_filter, limit)
        return APIResponse(
            success=True,
            message=f"Retrieved {result['count']} courses",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving courses: {str(e)}"
        )
