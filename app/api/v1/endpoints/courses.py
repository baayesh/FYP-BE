from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
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

