import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text, and_
from typing import Optional, List

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_student_user
from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.common import APIResponse, StudentDashboardStats, PerformanceData
from app.schemas.course import CourseListResponse
from app.schemas.assignment import AssignmentResponse
from app.schemas.lesson import LessonCompletionRequest, StudentLessonAnswerRequest, StudentLessonAnswerResponse
from app.models.user import User, UserRole
from app.models.course import Lesson
from app.models.student_lesson import StudentLesson
from app.services.student import StudentService

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

# Dashboard endpoints
@router.get("/dashboard/stats", response_model=APIResponse)
async def get_dashboard_stats(
    email: str = Query(..., description="User email to get dashboard stats for"),
    db: Session = Depends(get_db)
):
    """Get student dashboard statistics by email"""
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        student_service = StudentService(db)
        stats = student_service.get_dashboard_stats(user.id)
        
        return APIResponse(
            success=True,
            data=stats
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/performance", response_model=APIResponse)
async def get_performance_data(
    period: str = Query("month", regex="^(week|month|semester)$"),
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db)
):
    """Get student performance data"""
    try:
        student_service = StudentService(db)
        performance = student_service.get_performance_data(current_user.id, period)
        
        return APIResponse(
            success=True,
            data=performance
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Course endpoints
@router.get("/courses", response_model=APIResponse)
async def get_courses(
    status: Optional[str] = Query(None, regex="^(active|completed|archived)$"),
    search: Optional[str] = None,
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db)
):
    """Get all student courses"""
    try:
        student_service = StudentService(db)
        courses = student_service.get_courses(current_user.id, status, search)
        
        return APIResponse(
            success=True,
            data=courses
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/courses/{course_id}", response_model=APIResponse)
async def get_course_details(
    course_id: str,
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db)
):
    """Get course details"""
    try:
        student_service = StudentService(db)
        course = student_service.get_course_details(current_user.id, course_id)
        
        return APIResponse(
            success=True,
            data=course
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/courses/{course_id}/enroll", response_model=APIResponse)
async def enroll_in_course(
    course_id: str,
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db)
):
    """Enroll in course"""
    try:
        student_service = StudentService(db)
        result = student_service.enroll_in_course(current_user.id, course_id)
        
        return APIResponse(
            success=True,
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Grades endpoint
@router.get("/grades", response_model=APIResponse)
async def get_student_grades(
    email: str = Query(..., description="Student's email address"),
    db: Session = Depends(get_db)
):
    """Get student's grades with per-subject summaries and overall average"""
    try:
        student = get_student_by_email(email, db)
        student_service = StudentService(db)
        grades_data = student_service.get_grades(student.id, db)

        return APIResponse(
            success=True,
            data=grades_data,
            message="Grades retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Assignment endpoints
@router.get("/assignments", response_model=APIResponse)
async def get_assignments(
    email: str = Query(..., description="Student's email address"),
    status: Optional[str] = Query(None, regex="^(pending|submitted|graded)$"),
    course_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all assignments for a student by email"""
    try:
        student = get_student_by_email(email, db)
        student_service = StudentService(db)
        assignments = student_service.get_assignments(student.id, status, course_id)
        
        return APIResponse(
            success=True,
            data={
                "assignments": assignments,
                "count": len(assignments)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/assignments/{assignment_id}", response_model=APIResponse)
async def get_assignment_details(
    assignment_id: str,
    email: str = Query(..., description="Student's email address"),
    db: Session = Depends(get_db)
):
    """Get assignment details"""
    try:
        student = get_student_by_email(email, db)
        student_service = StudentService(db)
        assignment = student_service.get_assignment_details(student.id, assignment_id)
        
        return APIResponse(
            success=True,
            data=assignment
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


UPLOAD_DIR = "uploads/assignments"

@router.post("/assignments/{assignment_id}/submit", response_model=APIResponse)
async def submit_assignment(
    assignment_id: str,
    email: str = Query(..., description="Student's email address"),
    content: Optional[str] = Form(None),
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Submit an assignment — accepts multipart files + text content"""
    try:
        student = get_student_by_email(email, db)
        student_service = StudentService(db)

        file_data = []
        if files:
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            for f in files:
                if f.filename:
                    ext = os.path.splitext(f.filename)[1]
                    saved_name = f"{uuid.uuid4()}{ext}"
                    file_path = os.path.join(UPLOAD_DIR, saved_name)
                    with open(file_path, "wb") as buffer:
                        buffer.write(await f.read())
                    file_data.append({
                        "name": f.filename,
                        "url": file_path,
                        "size": os.path.getsize(file_path),
                    })

        result = student_service.submit_assignment(
            student_id=str(student.id),
            assignment_id=assignment_id,
            content=content,
            files=file_data if file_data else None,
        )
        return APIResponse(
            success=True,
            data=result,
            message="Assignment submitted successfully"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Lesson endpoints
@router.post("/lesson-completed/{lesson_id}", response_model=APIResponse)
async def mark_lesson_completed(
    lesson_id: str,
    student_id: str = Query(..., description="Student ID for lesson completion"),
    db: Session = Depends(get_db)
):
    try:
        print(f"Marking lesson completed for lesson_id: {lesson_id}")
        
        student_service = StudentService(db)
        quiz_questions = student_service.generate_lesson_quiz(lesson_id, student_id)
        
        return APIResponse(
            success=True,
            data={"message": quiz_questions},
            message="Lesson completion request received"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Error in mark_lesson_completed: {type(e).__name__} - {str(e)}")
        return APIResponse(
            success=False,
            message=f"Error: {str(e)}"
        )

# Submit lesson answers
@router.post("/submit-lesson-answers", response_model=APIResponse)
async def submit_lesson_answers(
    request: StudentLessonAnswerRequest,
    repetition_quiz: str = Query(..., description="Type of repetition quiz"),
    db: Session = Depends(get_db)
):
    """Submit student answers for a lesson"""
    try:
        student_service = StudentService(db)
        result = student_service.submit_lesson_answers(
            request.lesson_id,
            request.student_id,
            request.answers,
            repetition_quiz
        )
        
        return APIResponse(
            success=True,
            data=result,
            message=f"Lesson answers submitted successfully. AI Score: {result['score']}/10. Quiz Type: {repetition_quiz}"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get spaced repetition quizzes
@router.get("/spaced-repetition-quizzes", response_model=APIResponse)
async def get_spaced_repetition_quizzes(
    student_id: str = Query(..., description="Student ID to get spaced repetition quizzes for"),
    db: Session = Depends(get_db)
):
    """Get spaced repetition quizzes for a student"""
    try:
        student_service = StudentService(db)
        result = student_service.get_spaced_repetition_quizzes(student_id)
        
        return APIResponse(
            success=True,
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get spaced repetition quiz (singular)
@router.get("/get-spaced-repetition-quiz", response_model=APIResponse)
async def get_spaced_repetition_quiz(
    student_id: str = Query(..., description="Student ID to get spaced repetition quiz for"),
    db: Session = Depends(get_db)
):
    """Get spaced repetition quiz for a student"""
    try:
        student_service = StudentService(db)
        result = student_service.get_spaced_repetition_quizzes(student_id)
        
        return APIResponse(
            success=True,
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
