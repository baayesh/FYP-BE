import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models.user import User, UserRole
from app.models.course import Course, CourseEnrollment, EnrollmentStatus
from app.models.assignment import Assignment, AssignmentSubmission, AssignmentEnrollment
from app.models.forum import ForumThread, ForumReply, ThreadCategory
from app.core.exceptions import NotFoundError


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


class TeacherForumService:
    def __init__(self, db: Session):
        self.db = db

    def get_threads(self, course_id: Optional[str] = None) -> Dict[str, Any]:
        query = (
            self.db.query(
                ForumThread,
                User,
                Course,
                func.count(ForumReply.id).label("reply_count")
            )
            .join(User, ForumThread.author_id == User.id)
            .join(Course, ForumThread.course_id == Course.id)
            .outerjoin(ForumReply, ForumReply.thread_id == ForumThread.id)
            .group_by(ForumThread.id, User.id, Course.id)
            .order_by(ForumThread.is_pinned.desc(), ForumThread.created_at.desc())
        )

        if course_id:
            query = query.filter(ForumThread.course_id == course_id)

        results = query.all()

        threads = []
        for thread, author, course, reply_count in results:
            threads.append(self._thread_to_dict(thread, author, course, reply_count))

        total_replies = sum(t["replies"] for t in threads)
        total_likes = sum(t["likes"] for t in threads)
        total_pinned = sum(1 for t in threads if t["is_pinned"])

        return {
            "threads": threads,
            "total": len(threads),
            "total_replies": total_replies,
            "total_pinned": total_pinned,
            "total_likes": total_likes,
        }

    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        result = (
            self.db.query(
                ForumThread,
                User,
                Course,
                func.count(ForumReply.id).label("reply_count")
            )
            .join(User, ForumThread.author_id == User.id)
            .join(Course, ForumThread.course_id == Course.id)
            .outerjoin(ForumReply, ForumReply.thread_id == ForumThread.id)
            .filter(ForumThread.id == thread_id)
            .group_by(ForumThread.id, User.id, Course.id)
            .first()
        )

        if not result:
            raise NotFoundError("Thread not found")

        thread, author, course, reply_count = result

        # Increment views
        thread.views += 1
        self.db.commit()

        return self._thread_to_dict(thread, author, course, reply_count)

    def toggle_pin(self, thread_id: str) -> Dict[str, Any]:
        thread = self.db.query(ForumThread).filter(ForumThread.id == thread_id).first()
        if not thread:
            raise NotFoundError("Thread not found")
        thread.is_pinned = not thread.is_pinned
        self.db.commit()
        return {"is_pinned": thread.is_pinned}

    def toggle_resolve(self, thread_id: str) -> Dict[str, Any]:
        thread = self.db.query(ForumThread).filter(ForumThread.id == thread_id).first()
        if not thread:
            raise NotFoundError("Thread not found")
        thread.is_resolved = not thread.is_resolved
        self.db.commit()
        return {"is_resolved": thread.is_resolved}

    def mark_reply_as_answer(self, reply_id: str, thread_id: str) -> Dict[str, Any]:
        thread = self.db.query(ForumThread).filter(ForumThread.id == thread_id).first()
        if not thread:
            raise NotFoundError("Thread not found")
        reply = self.db.query(ForumReply).filter(
            ForumReply.id == reply_id,
            ForumReply.thread_id == thread_id
        ).first()
        if not reply:
            raise NotFoundError("Reply not found")
        reply.is_answer = not reply.is_answer
        self.db.commit()
        return {"is_answer": reply.is_answer}

    def _thread_to_dict(self, thread: ForumThread, author: User, course: Course, reply_count: int) -> Dict[str, Any]:
        tags = []
        if thread.tags:
            try:
                tags = json.loads(thread.tags) if isinstance(thread.tags, str) else thread.tags
            except (json.JSONDecodeError, TypeError):
                tags = []

        return {
            "id": thread.id,
            "title": thread.title,
            "author": author.full_name,
            "author_id": author.id,
            "course": course.title,
            "course_id": course.id,
            "content": thread.content,
            "replies": reply_count,
            "likes": thread.likes or 0,
            "is_pinned": thread.is_pinned,
            "is_resolved": thread.is_resolved,
            "views": thread.views or 0,
            "createdAt": thread.created_at.isoformat() if thread.created_at else None,
            "tags": tags,
        }
