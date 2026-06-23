from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User, UserRole
from app.models.course import Course, CourseEnrollment, EnrollmentStatus
from app.models.assignment import Assignment, AssignmentSubmission, AssignmentEnrollment


class TeacherAssignmentService:
    def __init__(self, db: Session):
        self.db = db

    def create_assignment(
        self, teacher_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        teacher = self.db.query(User).filter(
            User.id == teacher_id,
            User.role == UserRole.TEACHER
        ).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")

        course = self.db.query(Course).filter(
            Course.id == data["course_id"],
            Course.teacher_id == teacher_id
        ).first()
        if not course:
            raise HTTPException(
                status_code=404,
                detail="Course not found or not taught by this teacher"
            )

        assignment = Assignment(
            course_id=data["course_id"],
            title=data["title"],
            description=data.get("description"),
            instructions=data.get("instructions"),
            due_date=data["due_date"],
            points=data["points"],
        )
        self.db.add(assignment)
        self.db.flush()

        enrolled_students = self.db.query(CourseEnrollment).filter(
            CourseEnrollment.course_id == data["course_id"],
            CourseEnrollment.status == EnrollmentStatus.ACTIVE
        ).all()

        for enrollment in enrolled_students:
            ae = AssignmentEnrollment(
                course_id=data["course_id"],
                student_id=enrollment.student_id,
                assignment_id=assignment.id,
                status="pending",
            )
            self.db.add(ae)

        self.db.commit()
        self.db.refresh(assignment)

        return {
            "id": assignment.id,
            "course_id": assignment.course_id,
            "title": assignment.title,
            "description": assignment.description,
            "instructions": assignment.instructions,
            "dueDate": assignment.due_date.strftime("%Y-%m-%d"),
            "points": assignment.points,
            "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
        }

    def get_teacher_assignments(self, teacher_id: str) -> List[Dict[str, Any]]:
        courses = self.db.query(Course).filter(Course.teacher_id == teacher_id).all()

        assignments_data = []
        now = datetime.utcnow()

        for course in courses:
            total_students = (
                self.db.query(func.count(CourseEnrollment.id))
                .filter(
                    CourseEnrollment.course_id == course.id,
                    CourseEnrollment.status == EnrollmentStatus.ACTIVE,
                )
                .scalar()
                or 0
            )

            assignments = (
                self.db.query(Assignment)
                .filter(Assignment.course_id == course.id)
                .order_by(Assignment.due_date.desc())
                .all()
            )

            for assignment in assignments:
                submissions = (
                    self.db.query(AssignmentSubmission)
                    .filter(AssignmentSubmission.assignment_id == assignment.id)
                    .all()
                )

                submitted_count = len(submissions)

                graded_submissions = [s for s in submissions if s.grade is not None]
                avg_score = (
                    round(
                        sum(float(s.grade) for s in graded_submissions)
                        / len(graded_submissions),
                        1,
                    )
                    if graded_submissions
                    else None
                )

                if submitted_count == 0:
                    status = "active"
                elif len(graded_submissions) == submitted_count:
                    status = "completed"
                elif len(graded_submissions) > 0 and len(graded_submissions) < submitted_count:
                    status = "grading"
                elif submitted_count > 0 and len(graded_submissions) == 0:
                    status = "grading"
                else:
                    status = "active"

                assignments_data.append(
                    {
                        "id": assignment.id,
                        "title": assignment.title,
                        "class": course.title,
                        "subject": course.category or "",
                        "dueDate": assignment.due_date.strftime("%Y-%m-%d"),
                        "status": status,
                        "submitted": submitted_count,
                        "total": total_students,
                        "avgScore": avg_score,
                    }
                )

        return assignments_data
