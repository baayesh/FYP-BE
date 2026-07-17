from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.attendance import AttendanceBulkCreate
from app.models.user import User, UserRole
from app.models.course import Course, Lesson
from app.services.attendance import AttendanceService

teacher_router = APIRouter()
parent_router = APIRouter()


def _verify_teacher(teacher_id: str, db: Session) -> User:
    teacher = db.query(User).filter(
        User.id == teacher_id,
        User.role == UserRole.TEACHER
    ).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher


def _verify_course_ownership(course_id: str, teacher_id: str, db: Session) -> Course:
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.teacher_id == teacher_id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or not taught by you")
    return course


@teacher_router.get("/courses/{course_id}/lessons", response_model=APIResponse)
async def get_course_lessons_for_attendance(
    course_id: str,
    teacher_id: str = Query(..., description="UUID of the teacher"),
    db: Session = Depends(get_db),
):
    """Get lessons for a course (for attendance lesson selector)"""
    try:
        _verify_teacher(teacher_id, db)
        course = _verify_course_ownership(course_id, teacher_id, db)

        lessons = db.query(Lesson).filter(Lesson.course_id == course_id).order_by(Lesson.order_index).all()
        return APIResponse(
            success=True,
            data={"lessons": [{"id": l.id, "title": l.title, "order_index": l.order_index} for l in lessons]},
            message=f"Found {len(lessons)} lesson(s)",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@teacher_router.get("/courses/{course_id}/students", response_model=APIResponse)
async def get_course_students(
    course_id: str,
    teacher_id: str = Query(..., description="UUID of the teacher"),
    db: Session = Depends(get_db),
):
    """Get list of active enrolled students for a course (for attendance marking)"""
    try:
        _verify_teacher(teacher_id, db)
        _verify_course_ownership(course_id, teacher_id, db)

        service = AttendanceService(db)
        students = service.get_students_for_course(course_id)
        return APIResponse(success=True, data={"students": students}, message=f"Found {len(students)} student(s)")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@teacher_router.get("/courses/{course_id}/attendance", response_model=APIResponse)
async def get_attendance(
    course_id: str,
    lesson_id: str = Query(..., description="Lesson ID"),
    date_val: date = Query(..., alias="date", description="Date of the lesson session"),
    teacher_id: str = Query(..., description="UUID of the teacher"),
    db: Session = Depends(get_db),
):
    """Get attendance records for a specific lesson session"""
    try:
        _verify_teacher(teacher_id, db)
        course = _verify_course_ownership(course_id, teacher_id, db)

        lesson = db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.course_id == course_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found in this course")

        service = AttendanceService(db)
        records = service.get_attendance_records(course_id, lesson_id, date_val)
        summary = service.get_attendance_summary(course_id, lesson_id, date_val)
        return APIResponse(
            success=True,
            data={
                "records": records,
                "summary": summary,
                "course_title": course.title,
                "lesson_title": lesson.title,
            },
            message="Attendance records retrieved",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@teacher_router.post("/courses/{course_id}/attendance", response_model=APIResponse)
async def mark_attendance(
    course_id: str,
    body: AttendanceBulkCreate,
    teacher_id: str = Query(..., description="UUID of the teacher"),
    db: Session = Depends(get_db),
):
    """Bulk mark attendance for a lesson session (upsert)"""
    try:
        teacher = _verify_teacher(teacher_id, db)
        _verify_course_ownership(course_id, teacher_id, db)

        lesson = db.query(Lesson).filter(Lesson.id == body.lesson_id, Lesson.course_id == course_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found in this course")

        service = AttendanceService(db)
        saved = service.bulk_mark_attendance(
            course_id=course_id,
            lesson_id=body.lesson_id,
            date_val=body.date,
            records=[r.dict() for r in body.records],
            marked_by=teacher.id,
        )
        summary = service.get_attendance_summary(course_id, body.lesson_id, body.date)
        return APIResponse(
            success=True,
            data={"records": saved, "summary": summary},
            message=f"Attendance saved for {len(saved)} student(s)",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ── Parent Endpoints ──


@parent_router.get("/attendance/{student_id}", response_model=APIResponse)
async def get_student_attendance_summary(
    student_id: str,
    course_id: Optional[str] = Query(None, description="Optional course filter"),
    parent_id: str = Query(..., description="UUID of the parent"),
    db: Session = Depends(get_db),
):
    """Get attendance summary for a child (parent view)"""
    try:
        parent = db.query(User).filter(
            User.id == parent_id,
            User.role == UserRole.PARENT
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent not found")

        from app.models.calendar_event import ParentChildRelationship
        linked = db.query(ParentChildRelationship).filter(
            ParentChildRelationship.parent_id == parent_id,
            ParentChildRelationship.child_id == student_id,
        ).first()
        if not linked:
            raise HTTPException(status_code=403, detail="This student is not your child")

        service = AttendanceService(db)
        summaries = service.get_student_summary(student_id, course_id)
        return APIResponse(success=True, data={"summaries": summaries}, message="Student attendance summary retrieved")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@parent_router.get("/attendance/{student_id}/history", response_model=APIResponse)
async def get_student_attendance_history(
    student_id: str,
    course_id: Optional[str] = Query(None, description="Optional course filter"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    parent_id: str = Query(..., description="UUID of the parent"),
    db: Session = Depends(get_db),
):
    """Get attendance history for a child (parent view)"""
    try:
        parent = db.query(User).filter(
            User.id == parent_id,
            User.role == UserRole.PARENT
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent not found")

        from app.models.calendar_event import ParentChildRelationship
        linked = db.query(ParentChildRelationship).filter(
            ParentChildRelationship.parent_id == parent_id,
            ParentChildRelationship.child_id == student_id,
        ).first()
        if not linked:
            raise HTTPException(status_code=403, detail="This student is not your child")

        service = AttendanceService(db)
        history = service.get_student_history(student_id, course_id, page, limit)
        return APIResponse(success=True, data=history, message="Student attendance history retrieved")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
