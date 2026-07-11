from typing import List, Dict, Any, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from fastapi import HTTPException

from app.models.attendance import Attendance, AttendanceStatus
from app.models.user import User
from app.models.course import Course, CourseEnrollment, EnrollmentStatus, Lesson


class AttendanceService:
    def __init__(self, db: Session):
        """Initialize the attendance service with a database session."""
        self.db = db

    def get_students_for_course(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all enrolled students for a given course."""
        enrollments = (
            self.db.query(CourseEnrollment)
            .options(joinedload(CourseEnrollment.student))
            .filter(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.status == EnrollmentStatus.ACTIVE,
            )
            .all()
        )
        return [
            {
                "student_id": e.student.id,
                "first_name": e.student.first_name,
                "last_name": e.student.last_name,
                "email": e.student.email,
            }
            for e in enrollments
        ]

    def get_attendance_records(
        self, course_id: str, lesson_id: str, date_val: date
    ) -> List[Dict[str, Any]]:
        """Get attendance records for a specific course, lesson, and date."""
        records = (
            self.db.query(Attendance)
            .options(joinedload(Attendance.student), joinedload(Attendance.lesson))
            .filter(
                Attendance.course_id == course_id,
                Attendance.lesson_id == lesson_id,
                Attendance.date == date_val,
            )
            .all()
        )
        return [
            {
                "id": r.id,
                "student_id": r.student_id,
                "student_name": f"{r.student.first_name} {r.student.last_name}",
                "lesson_id": r.lesson_id,
                "lesson_title": r.lesson.title if r.lesson else None,
                "status": r.status.value,
                "date": r.date.isoformat(),
                "check_in_time": r.check_in_time.isoformat() if r.check_in_time else None,
                "notes": r.notes,
                "marked_at": r.marked_at.isoformat() if r.marked_at else None,
            }
            for r in records
        ]

    def bulk_mark_attendance(
        self,
        course_id: str,
        lesson_id: str,
        date_val: date,
        records: List[Dict[str, Any]],
        marked_by: str,
    ) -> List[Dict[str, Any]]:
        """Bulk create or update attendance records for a lesson."""
        saved = []
        for rec in records:
            status_val = rec["status"].upper() if isinstance(rec["status"], str) else rec["status"].value
            if status_val not in [s.value.upper() for s in AttendanceStatus]:
                raise HTTPException(status_code=400, detail=f"Invalid status: {rec['status']}")

            existing = (
                self.db.query(Attendance)
                .filter(
                    Attendance.course_id == course_id,
                    Attendance.lesson_id == lesson_id,
                    Attendance.student_id == rec["student_id"],
                )
                .first()
            )

            if existing:
                existing.status = AttendanceStatus[status_val]
                existing.marked_by = marked_by
                existing.marked_at = datetime.utcnow()
                existing.date = date_val
                if rec.get("notes") is not None:
                    existing.notes = rec.get("notes")
                if rec.get("check_in_time") is not None:
                    existing.check_in_time = rec.get("check_in_time")
                att = existing
            else:
                att = Attendance(
                    course_id=course_id,
                    lesson_id=lesson_id,
                    student_id=rec["student_id"],
                    date=date_val,
                    status=AttendanceStatus[status_val],
                    check_in_time=rec.get("check_in_time"),
                    notes=rec.get("notes"),
                    marked_by=marked_by,
                )
                self.db.add(att)

            self.db.flush()
            self.db.refresh(att, attribute_names=["student", "lesson"])
            saved.append(att)

        self.db.commit()

        return [
            {
                "id": a.id,
                "student_id": a.student_id,
                "student_name": f"{a.student.first_name} {a.student.last_name}" if a.student else "",
                "status": a.status.value,
                "date": a.date.isoformat(),
            }
            for a in saved
        ]

    def get_attendance_summary(
        self, course_id: str, lesson_id: str, date_val: date
    ) -> Dict[str, Any]:
        """Get an attendance summary with counts by status for a lesson."""
        counts = (
            self.db.query(
                Attendance.status,
                func.count(Attendance.id).label("count"),
            )
            .filter(
                Attendance.course_id == course_id,
                Attendance.lesson_id == lesson_id,
                Attendance.date == date_val,
            )
            .group_by(Attendance.status)
            .all()
        )

        total_enrolled = (
            self.db.query(func.count(CourseEnrollment.id))
            .filter(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.status == EnrollmentStatus.ACTIVE,
            )
            .scalar()
            or 0
        )

        status_map = {s.value: 0 for s in AttendanceStatus}
        for row in counts:
            status_map[row.status.value] = row.count

        total_marked = sum(status_map.values())
        rate = round((status_map["present"] / total_marked * 100), 1) if total_marked > 0 else 0.0

        return {
            "total": total_enrolled,
            "present": status_map["present"],
            "absent": status_map["absent"],
            "late": status_map["late"],
            "excused": status_map["excused"],
            "rate": rate,
        }

    def get_student_summary(
        self, student_id: str, course_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get attendance summary grouped by course for a specific student."""
        filters = [Attendance.student_id == student_id]
        if course_id:
            filters.append(Attendance.course_id == course_id)

        query = (
            self.db.query(
                Attendance.course_id,
                Course.title.label("course_title"),
                func.count(Attendance.id).label("total_sessions"),
                func.sum(
                    func.if_(Attendance.status == AttendanceStatus.PRESENT, 1, 0)
                ).label("present"),
                func.sum(
                    func.if_(Attendance.status == AttendanceStatus.ABSENT, 1, 0)
                ).label("absent"),
                func.sum(
                    func.if_(Attendance.status == AttendanceStatus.LATE, 1, 0)
                ).label("late"),
                func.sum(
                    func.if_(Attendance.status == AttendanceStatus.EXCUSED, 1, 0)
                ).label("excused"),
            )
            .join(Course, Course.id == Attendance.course_id)
            .filter(*filters)
            .group_by(Attendance.course_id, Course.title)
        )

        results = []
        for row in query.all():
            total = row.present + row.absent + row.late + row.excused
            rate = round((row.present / total * 100), 1) if total > 0 else 0.0
            results.append(
                {
                    "course_id": row.course_id,
                    "course_title": row.course_title,
                    "total_sessions": row.total_sessions,
                    "present": row.present,
                    "absent": row.absent,
                    "late": row.late,
                    "excused": row.excused,
                    "rate": rate,
                }
            )
        return results

    def get_student_history(
        self, student_id: str, course_id: Optional[str] = None, page: int = 1, limit: int = 20
    ) -> Dict[str, Any]:
        """Get paginated attendance history for a specific student."""
        filters = [Attendance.student_id == student_id]
        if course_id:
            filters.append(Attendance.course_id == course_id)

        query = (
            self.db.query(Attendance)
            .options(joinedload(Attendance.lesson))
            .filter(*filters)
            .order_by(Attendance.date.desc(), Attendance.marked_at.desc())
        )

        total = query.count()
        items = query.offset((page - 1) * limit).limit(limit).all()

        return {
            "items": [
                {
                    "id": a.id,
                    "lesson_title": a.lesson.title if a.lesson else None,
                    "date": a.date.isoformat(),
                    "status": a.status.value,
                    "marked_at": a.marked_at.isoformat() if a.marked_at else None,
                }
                for a in items
            ],
            "total": total,
            "page": page,
            "limit": limit,
        }

    def get_course_history(
        self, course_id: str, page: int = 1, limit: int = 20
    ) -> Dict[str, Any]:
        """Get paginated attendance history grouped by lesson for a course."""
        subq = (
            self.db.query(
                Attendance.lesson_id,
                Attendance.date,
                Lesson.title.label("lesson_title"),
                func.count(Attendance.id).label("total_marked"),
                func.sum(
                    func.if_(Attendance.status == AttendanceStatus.PRESENT, 1, 0)
                ).label("present_count"),
            )
            .join(Lesson, Lesson.id == Attendance.lesson_id)
            .filter(Attendance.course_id == course_id)
            .group_by(Attendance.lesson_id, Attendance.date, Lesson.title)
            .order_by(Attendance.date.desc(), Attendance.lesson_id)
            .subquery()
        )

        total_query = self.db.query(func.count()).select_from(subq).scalar() or 0

        rows = (
            self.db.query(subq)
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        items = []
        for r in rows:
            rate = round((r._mapping["present_count"] / r._mapping["total_marked"] * 100), 1) if r._mapping["total_marked"] > 0 else 0.0
            items.append(
                {
                    "lesson_id": r._mapping["lesson_id"],
                    "lesson_title": r._mapping["lesson_title"],
                    "date": r._mapping["date"].isoformat(),
                    "total_marked": r._mapping["total_marked"],
                    "present_count": r._mapping["present_count"],
                    "rate": rate,
                }
            )

        return {
            "items": items,
            "total": total_query,
            "page": page,
            "limit": limit,
        }
