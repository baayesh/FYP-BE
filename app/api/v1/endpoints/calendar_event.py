from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.models.user import User, UserRole
from app.models.course import CourseEnrollment
from app.models.calendar_event import CalendarEvent

router = APIRouter()


@router.get("/calendar-events", response_model=APIResponse)
def get_calendar_events(
    email: str = Query(..., description="Student email"),
    start_date: Optional[str] = Query(None, description="Filter start (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter end (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(
        and_(User.email == email, User.role == UserRole.STUDENT)
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found with the provided email"
        )

    enrolled_course_ids = [
        row.course_id
        for row in db.query(CourseEnrollment.course_id).filter(
            CourseEnrollment.student_id == user.id,
            CourseEnrollment.status == "ACTIVE"
        ).all()
    ]

    query = db.query(CalendarEvent).options(
        joinedload(CalendarEvent.course),
        joinedload(CalendarEvent.creator),
    )

    filters = []
    if enrolled_course_ids:
        filters.append(CalendarEvent.course_id.in_(enrolled_course_ids))
    else:
        filters.append(CalendarEvent.course_id.is_(None))

    if start_date:
        try:
            dt = datetime.strptime(start_date, "%Y-%m-%d")
            filters.append(CalendarEvent.start_time >= dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )

    if end_date:
        try:
            dt = datetime.strptime(end_date, "%Y-%m-%d")
            filters.append(CalendarEvent.end_time <= dt.replace(hour=23, minute=59, second=59))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )

    query = query.filter(and_(*filters)).order_by(CalendarEvent.start_time.asc())

    events = query.all()

    result = []
    for event in events:
        instructor = None
        if event.course and event.course.instructor:
            instructor = event.course.instructor
        elif event.creator:
            instructor = f"{event.creator.first_name} {event.creator.last_name}"

        result.append({
            "id": str(event.id),
            "title": event.title,
            "description": event.description,
            "type": event.type.value if hasattr(event.type, 'value') else str(event.type),
            "start_time": event.start_time.isoformat() if event.start_time else None,
            "end_time": event.end_time.isoformat() if event.end_time else None,
            "location": event.location,
            "link": event.link,
            "instructor": instructor,
            "course_id": str(event.course_id) if event.course_id else None,
            "course_name": event.course.title if event.course else None,
            "creator_id": str(event.creator_id),
            "created_at": event.created_at.isoformat() if event.created_at else None,
        })

    return APIResponse(
        success=True,
        data={"events": result, "count": len(result)},
        message="Calendar events retrieved successfully"
    )
