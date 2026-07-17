from fastapi import APIRouter, Depends, Query, Path, status, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.dependencies import get_db
from app.repositories.course import CourseRepository, LessonRepository
from app.repositories.user import UserRepository
from app.schemas.common import APIResponse
from app.schemas.lesson import LessonCreate
from app.models.user import UserRole

router = APIRouter()

ERR_COURSE_NOT_FOUND = "Course not found"
ERR_LESSON_NOT_FOUND = "Lesson not found"


def _minutes_from_text(duration: Optional[str]) -> Optional[int]:
    if not duration:
        return None
    try:
        digits = ''.join(ch for ch in duration if ch.isdigit())
        return int(digits) if digits else None
    except Exception:
        return None


def _lesson_to_response(lesson, progress_map) -> dict:
    return {
        "id": lesson.id,
        "course_id": lesson.course_id,
        "title": lesson.title,
        "description": lesson.description,
        "content": lesson.content,
        "duration": lesson.duration_text or (f"{lesson.duration} min" if lesson.duration else None),
        "status": lesson.status,
        "video_link": lesson.video_link,
        "quizzes": lesson.quizzes_json or [],
        "assignments": lesson.assignments_json or [],
        "order_index": lesson.order_index,
        "progress": float(progress_map.get(str(lesson.id), 0.0)),
    }


@router.get("/{course_id}/lessons", response_model=APIResponse)
def list_lessons(
    course_id: str = Path(..., description="Course ID"),
    email: str = Query(..., description="User email for progress context"),
    db: Session = Depends(get_db)
):
    lesson_repo = LessonRepository(db)
    course_repo = CourseRepository(db)
    user_repo = UserRepository(db)

    course = course_repo.get_by_id(course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERR_COURSE_NOT_FOUND)

    lessons = lesson_repo.get_by_course(course_id)

    progress_map = {}
    user = user_repo.get_by_email(email)
    if user and user.role == UserRole.STUDENT:
        progresses = lesson_repo.get_student_progress(user.id, course_id)
        for p in progresses:
            progress_map[str(p.lesson_id)] = 100.0 if p.completed else min(float(p.time_spent or 0) / max(lesson.duration or 1, 1) * 100.0, 100.0)

    payload = [_lesson_to_response(lesson, progress_map) for lesson in lessons]
    return {"success": True, "data": {"lessons": payload, "count": len(payload)}, "message": f"Retrieved {len(payload)} lessons"}



@router.post("/{course_id}/lessons", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(
    course_id: str,
    payload: LessonCreate,
    db: Session = Depends(get_db)
):
    course_repo = CourseRepository(db)
    lesson_repo = LessonRepository(db)

    course = course_repo.get_by_id(course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERR_COURSE_NOT_FOUND)

    lesson_data = {
        "course_id": str(course_id),
        "title": payload.title,
        "description": payload.description,
        "content": payload.content,
        "status": payload.status or "unlocked",
        "video_link": payload.video_link,
        "duration": _minutes_from_text(payload.duration),
        "duration_text": payload.duration,
        "quizzes_json": [q.dict() for q in payload.quizzes],
        "assignments_json": [a.dict() for a in payload.assignments],
        "type": "VIDEO",
        "order_index": payload.order_index,
    }

    lesson = lesson_repo.create(lesson_data)
    return {"success": True, "data": _lesson_to_response(lesson, {}), "message": "Lesson created"}

