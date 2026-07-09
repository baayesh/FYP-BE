from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from sqlalchemy import func

from app.core.database import get_db
from app.core.dependencies import get_teacher_user
from app.schemas.common import APIResponse
from app.core.exceptions import NotFoundError
from app.models.user import User, UserRole
from app.services.teacher import TeacherForumService
from app.models.course import Course, CourseStatus, CourseEnrollment, EnrollmentStatus
from app.models.assignment import Assignment, AssignmentSubmission, AssignmentStatus
from app.models.grade import Grade, GradeItemType
from app.services.teacher_stats import TeacherStatsService
from app.services.teacher import TeacherAssignmentService
from app.services.performance_service import PerformanceService

from pydantic import BaseModel, Field
from datetime import datetime
from app.models.course import Lesson, LessonType

router = APIRouter()

# New schema for lesson creation request
class QuizItem(BaseModel):
    question: str
    answer: str

class AssignmentItem(BaseModel):
    title: str
    description: str

class CreateLessonRequest(BaseModel):
    title: str = Field(..., min_length=1)
    type: str = Field(..., pattern="^(VIDEO|READING|QUIZ|ASSIGNMENT)$")
    content: str
    duration: int = Field(..., gt=0)
    status: str = Field("unlocked", pattern="^(locked|unlocked)$")
    quizzes: List[QuizItem] = []
    assignments: List[AssignmentItem] = []
    video_link: Optional[str] = None

# Dashboard endpoints
@router.get("/dashboard/stats", response_model=APIResponse)
async def get_dashboard_stats(
    teacher_id: str = Query(..., description="UUID of the teacher"),
    db: Session = Depends(get_db)
):
    """Get teacher dashboard statistics"""
    try:
        # Verify teacher exists
        teacher = db.query(User).filter(
            User.id == teacher_id,
            User.role == UserRole.TEACHER
        ).first()
        
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        
        service = TeacherStatsService(db)
        stats = service.get_dashboard_stats(teacher_id)
        return APIResponse(success=True, data=stats, message="Teacher dashboard data retrieved successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboard/stats/snapshot", response_model=APIResponse)
async def capture_teacher_stats_snapshot(
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db)
):
    """Capture and persist today's teacher stats snapshot and minimal timeseries."""
    try:
        service = TeacherStatsService(db)
        saved = service.capture_snapshot(current_user.id)
        return APIResponse(success=True, data=saved, message="Snapshot saved")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Course management endpoints
@router.get("/courses", response_model=APIResponse)
async def get_teacher_courses(
    teacher_id: str = Query(..., description="UUID of the teacher"),
    status: Optional[str] = Query(None, regex="^(active|archived|draft)$"),
    db: Session = Depends(get_db)
):
    """Get courses taught by a teacher specified by ID"""
    try:
        # Verify teacher exists and is a teacher
        teacher = db.query(User).filter(
            User.id == teacher_id,
            User.role == UserRole.TEACHER
        ).first()
        
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        
        # Build course query
        query = db.query(Course).filter(Course.teacher_id == teacher_id)
        
        # Optional status filter
        if status:
            query = query.filter(Course.status == CourseStatus[status.upper()])
        
        # Order by created date (newest first)
        courses = query.order_by(Course.created_at.desc()).all()
        
        # Build response data with enrollment counts
        courses_data = []
        for course in courses:
            # Count active enrollments
            enrolled_count = db.query(func.count(CourseEnrollment.id)).filter(
                CourseEnrollment.course_id == course.id,
                CourseEnrollment.status == EnrollmentStatus.ACTIVE
            ).scalar() or 0
            
            course_dict = {
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "category": course.category,
                "level": course.level,
                "duration": course.duration,
                "thumbnail_url": course.thumbnail,
                "status": course.status.value,
                "enrolled_students": enrolled_count,
                "total_lessons": len(course.lessons) if course.lessons else 0,
                "created_at": course.created_at.isoformat() if course.created_at else None,
                "updated_at": course.updated_at.isoformat() if course.updated_at else None
            }
            courses_data.append(course_dict)
        
        return APIResponse(
            success=True, 
            data={"courses": courses_data},
            message=f"Found {len(courses_data)} course(s) for teacher {teacher.first_name} {teacher.last_name}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/courses/{course_id}", response_model=APIResponse)
async def get_course_by_id(
    course_id: str,
    teacher_id: str = Query(..., description="UUID of the teacher (for authorization)"),
    db: Session = Depends(get_db)
):
    """Get a specific course by ID with its lessons (only if taught by the specified teacher)"""
    try:
        # Verify teacher exists and is a teacher
        teacher = db.query(User).filter(
            User.id == teacher_id,
            User.role == UserRole.TEACHER
        ).first()
        
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        
        # Get the course with lessons (eager loading)
        course = db.query(Course).options(joinedload(Course.lessons)).filter(
            Course.id == course_id,
            Course.teacher_id == teacher_id
        ).first()
        
        if not course:
            raise HTTPException(status_code=404, detail="Course not found or not taught by this teacher")
        
        # Count active enrollments
        enrolled_count = db.query(func.count(CourseEnrollment.id)).filter(
            CourseEnrollment.course_id == course.id,
            CourseEnrollment.status == EnrollmentStatus.ACTIVE
        ).scalar() or 0
        
        # Build lessons data
        lessons_data = []
        if course.lessons:
            # Sort lessons by order_index
            sorted_lessons = sorted(course.lessons, key=lambda l: l.order_index)
            for lesson in sorted_lessons:
                lesson_dict = {
                    "id": lesson.id,
                    "title": lesson.title,
                    "type": lesson.type.value,
                    "description": lesson.description,
                    "content": lesson.content,
                    "status": lesson.status,
                    "duration": lesson.duration,
                    "duration_text": lesson.duration_text,
                    "video_link": lesson.video_link,
                    "quizzes_json": lesson.quizzes_json,
                    "assignments_json": lesson.assignments_json,
                    "order_index": lesson.order_index,
                    "created_at": lesson.created_at.isoformat() if lesson.created_at else None,
                    "updated_at": lesson.updated_at.isoformat() if lesson.updated_at else None
                }
                lessons_data.append(lesson_dict)
        
        # Build course data with lessons
        course_data = {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "level": course.level,
            "duration": course.duration,
            "thumbnail_url": course.thumbnail,
            "status": course.status.value,
            "enrolled_students": enrolled_count,
            "total_lessons": len(lessons_data),
            "lessons": lessons_data,  # Include lessons array
            "created_at": course.created_at.isoformat() if course.created_at else None,
            "updated_at": course.updated_at.isoformat() if course.updated_at else None
        }
        
        return APIResponse(
            success=True, 
            data={"course": course_data},
            message=f"Course '{course.title}' with {len(lessons_data)} lessons found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/courses", response_model=APIResponse)
async def create_course(
    course_data: dict,  # Use proper schema
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db)
):
    """Create a new course"""
    try:
        # Implementation here
        return APIResponse(success=True, message="Course created successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New endpoint for creating a lesson
@router.post("/courses/{course_id}/lessons", response_model=APIResponse)
async def create_lesson(
    course_id: str,
    lesson_data: CreateLessonRequest,
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db)
):
    """Create a new lesson for a specific course (only if taught by the authenticated teacher)"""
    try:
        # Verify the course exists and is taught by the current teacher
        course = db.query(Course).filter(
            Course.id == course_id,
            Course.teacher_id == current_user.id
        ).first()
        
        if not course:
            raise HTTPException(status_code=404, detail="Course not found or not taught by this teacher")
        
        # Determine the next order_index for the course
        max_order = db.query(func.max(Lesson.order_index)).filter(Lesson.course_id == course_id).scalar() or 0
        next_order = max_order + 1
        
        # Create the lesson
        new_lesson = Lesson(
            course_id=course_id,
            title=lesson_data.title,
            type=LessonType[lesson_data.type.upper()],
            content=lesson_data.content,
            duration=lesson_data.duration,
            status=lesson_data.status,
            video_link=lesson_data.video_link,
            quizzes_json=lesson_data.quizzes,
            assignments_json=lesson_data.assignments,
            order_index=next_order
        )
        
        db.add(new_lesson)
        db.commit()
        db.refresh(new_lesson)
        
        # Build response data
        lesson_dict = {
            "id": new_lesson.id,
            "title": new_lesson.title,
            "type": new_lesson.type.value,
            "content": new_lesson.content,
            "duration": new_lesson.duration,
            "status": new_lesson.status,
            "video_link": new_lesson.video_link,
            "quizzes_json": new_lesson.quizzes_json,
            "assignments_json": new_lesson.assignments_json,
            "order_index": new_lesson.order_index,
            "created_at": new_lesson.created_at.isoformat() if new_lesson.created_at else None,
            "updated_at": new_lesson.updated_at.isoformat() if new_lesson.updated_at else None
        }
        
        return APIResponse(
            success=True,
            data={"lesson": lesson_dict},
            message="Lesson created successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ── Forum Endpoints ──

@router.get("/forum/threads", response_model=APIResponse)
async def teacher_get_threads(
    course_id: Optional[str] = Query(None, description="Filter by course ID"),
    db: Session = Depends(get_db),
):
    """Get all forum threads (teacher)"""
    try:
        service = TeacherForumService(db)
        result = service.get_threads(course_id)
        return APIResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forum/threads/{thread_id}", response_model=APIResponse)
async def teacher_get_thread(
    thread_id: str,
    db: Session = Depends(get_db),
):
    """Get a single forum thread by ID (teacher)"""
    try:
        service = TeacherForumService(db)
        thread = service.get_thread(thread_id)
        return APIResponse(success=True, data=thread)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forum/threads/{thread_id}/pin", response_model=APIResponse)
async def teacher_toggle_pin(
    thread_id: str,
    db: Session = Depends(get_db),
):
    """Toggle pin status on a thread (teacher)"""
    try:
        service = TeacherForumService(db)
        result = service.toggle_pin(thread_id)
        return APIResponse(success=True, data=result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forum/threads/{thread_id}/resolve", response_model=APIResponse)
async def teacher_toggle_resolve(
    thread_id: str,
    db: Session = Depends(get_db),
):
    """Toggle resolved status on a thread (teacher)"""
    try:
        service = TeacherForumService(db)
        result = service.toggle_resolve(thread_id)
        return APIResponse(success=True, data=result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forum/threads/{thread_id}/replies/{reply_id}/mark-answer", response_model=APIResponse)
async def teacher_mark_as_answer(
    thread_id: str,
    reply_id: str,
    db: Session = Depends(get_db),
):
    """Mark/unmark a reply as the answer (teacher)"""
    try:
        service = TeacherForumService(db)
        result = service.mark_reply_as_answer(reply_id, thread_id)
        return APIResponse(success=True, data=result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---- Assignment management endpoints ----
@router.get("/assignments", response_model=APIResponse)
async def get_teacher_assignments(
    teacher_id: str = Query(..., description="UUID of the teacher"),
    db: Session = Depends(get_db)
):
    """Get all assignments for courses taught by a teacher"""
    try:
        teacher = db.query(User).filter(
            User.id == teacher_id,
            User.role == UserRole.TEACHER
        ).first()

        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")

        service = TeacherAssignmentService(db)
        assignments = service.get_teacher_assignments(teacher_id)

        return APIResponse(
            success=True,
            data={"assignments": assignments},
            message=f"Found {len(assignments)} assignment(s)"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CreateAssignmentRequest(BaseModel):
    course_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    instructions: Optional[str] = None
    due_date: datetime
    points: int = Field(..., ge=0)

@router.post("/assignments", response_model=APIResponse)
async def create_assignment(
    assignment_data: CreateAssignmentRequest,
    teacher_id: str = Query(..., description="UUID of the teacher"),
    db: Session = Depends(get_db)
):
    """Create a new assignment for a course taught by the teacher"""
    try:
        service = TeacherAssignmentService(db)
        assignment = service.create_assignment(teacher_id, assignment_data.dict())

        return APIResponse(
            success=True,
            data={"assignment": assignment},
            message="Assignment created successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Grading Schema ──

class GradeSubmissionRequest(BaseModel):
    student_id: str = Field(..., description="ID of the student")
    grade: float = Field(..., ge=0, description="Numeric grade (percentage)")
    feedback: Optional[str] = Field(None, description="Teacher feedback")
    max_score: float = Field(100.0, ge=1, description="Maximum possible score")


# ── Grading Endpoint ──

@router.post("/assignments/{assignment_id}/grade", response_model=APIResponse)
async def grade_assignment(
    assignment_id: str,
    body: GradeSubmissionRequest,
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db)
):
    """Grade a student's assignment submission (Teacher only)."""
    try:
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        course = db.query(Course).filter(
            Course.id == assignment.course_id,
            Course.teacher_id == current_user.id
        ).first()
        if not course:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to grade this assignment"
            )

        submission = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.student_id == body.student_id
        ).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        percentage = min(body.grade, 100.0)
        points_earned = round((percentage / 100.0) * body.max_score, 2)

        submission.grade = percentage
        submission.feedback = body.feedback
        submission.status = AssignmentStatus.GRADED

        grade_record = Grade(
            student_id=body.student_id,
            course_id=assignment.course_id,
            item_type=GradeItemType.ASSIGNMENT,
            item_id=assignment_id,
            grade=percentage,
            points_earned=points_earned,
            points_possible=body.max_score,
            graded_by=current_user.id,
            graded_at=datetime.utcnow(),
        )
        db.add(grade_record)
        db.commit()

        try:
            PerformanceService(db).update_trend(body.student_id)
        except Exception:
            pass

        return APIResponse(
            success=True,
            message="Assignment graded successfully",
            data={
                "submission_id": submission.id,
                "grade": percentage,
                "points_earned": points_earned,
                "points_possible": body.max_score,
                "feedback": body.feedback,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))