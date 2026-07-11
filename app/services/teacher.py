import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, date, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, distinct
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models.user import User, UserRole
from app.models.course import Course, CourseEnrollment, EnrollmentStatus, Lesson
from app.models.assignment import Assignment, AssignmentSubmission, AssignmentEnrollment, AssignmentStatus
from app.models.forum import ForumThread, ForumReply, ThreadCategory
from app.models.grade import Grade
from app.models.calendar_event import CalendarEvent, EventType
from app.models.activity_log import ActivityLog
from app.models.teacher import TeacherStats, TeacherStatTimeseries
from app.core.exceptions import NotFoundError


class TeacherAssignmentService:
    def __init__(self, db: Session):
        """Initialize the teacher assignment service with a database session."""
        self.db = db

    def create_assignment(
        self, teacher_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new assignment for a course taught by the teacher."""
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
        """Get all assignments across courses taught by the teacher."""
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
        """Initialize the teacher forum service with a database session."""
        self.db = db

    def get_threads(self, course_id: Optional[str] = None) -> Dict[str, Any]:
        """Get all forum threads, optionally filtered by course."""
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
        """Get a single forum thread by ID and increment its view count."""
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
        """Toggle the pinned status of a forum thread."""
        thread = self.db.query(ForumThread).filter(ForumThread.id == thread_id).first()
        if not thread:
            raise NotFoundError("Thread not found")
        thread.is_pinned = not thread.is_pinned
        self.db.commit()
        return {"is_pinned": thread.is_pinned}

    def toggle_resolve(self, thread_id: str) -> Dict[str, Any]:
        """Toggle the resolved status of a forum thread."""
        thread = self.db.query(ForumThread).filter(ForumThread.id == thread_id).first()
        if not thread:
            raise NotFoundError("Thread not found")
        thread.is_resolved = not thread.is_resolved
        self.db.commit()
        return {"is_resolved": thread.is_resolved}

    def mark_reply_as_answer(self, reply_id: str, thread_id: str) -> Dict[str, Any]:
        """Toggle a reply as the accepted answer for a thread."""
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

    def get_replies(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all replies for a forum thread, ordered chronologically."""
        thread = self.db.query(ForumThread).filter(ForumThread.id == thread_id).first()
        if not thread:
            raise NotFoundError("Thread not found")

        results = (
            self.db.query(ForumReply, User)
            .join(User, ForumReply.author_id == User.id)
            .filter(ForumReply.thread_id == thread_id)
            .order_by(ForumReply.created_at.asc())
            .all()
        )

        return [
            {
                "id": reply.id,
                "thread_id": reply.thread_id,
                "content": reply.content,
                "author": author.full_name,
                "author_id": author.id,
                "is_answer": reply.is_answer,
                "parent_reply_id": reply.parent_reply_id,
                "created_at": reply.created_at.isoformat() if reply.created_at else None,
            }
            for reply, author in results
        ]

    def create_reply(self, thread_id: str, author_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new reply in a forum thread."""
        thread = self.db.query(ForumThread).filter(ForumThread.id == thread_id).first()
        if not thread:
            raise NotFoundError("Thread not found")

        reply = ForumReply(
            id=str(uuid4()),
            thread_id=thread_id,
            author_id=author_id,
            content=data["content"],
            parent_reply_id=data.get("parent_reply_id"),
        )
        self.db.add(reply)
        self.db.commit()
        self.db.refresh(reply)

        author = self.db.query(User).filter(User.id == author_id).first()

        return {
            "id": reply.id,
            "thread_id": reply.thread_id,
            "content": reply.content,
            "author": author.full_name if author else "",
            "author_id": author.id if author else "",
            "is_answer": reply.is_answer,
            "parent_reply_id": parent_reply_id,
            "created_at": reply.created_at.isoformat() if reply.created_at else None,
        }

    def like_thread(self, thread_id: str, user_id: str, liked: bool) -> Dict[str, Any]:
        """Increment or decrement the like count on a forum thread."""
        thread = self.db.query(ForumThread).filter(ForumThread.id == thread_id).first()
        if not thread:
            raise NotFoundError("Thread not found")
        if liked:
            thread.likes = (thread.likes or 0) + 1
        else:
            thread.likes = max(0, (thread.likes or 0) - 1)
        self.db.commit()
        return {"likes": thread.likes}

    def _thread_to_dict(self, thread: ForumThread, author: User, course: Course, reply_count: int) -> Dict[str, Any]:
        """Helper: serialize a forum thread and its metadata into a dictionary."""
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


class TeacherCourseService:
    def __init__(self, db: Session):
        """Initialize the teacher course service with a database session."""
        self.db = db

    def update_course(self, teacher_id: str, course_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a course with ownership verification."""
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        if str(course.teacher_id) != str(teacher_id):
            raise HTTPException(status_code=403, detail="You can only update your own courses")

        updatable = {"title", "description", "category", "level", "duration", "thumbnail", "status"}
        for key, value in data.items():
            if key in updatable and value is not None:
                setattr(course, key, value)

        self.db.commit()
        self.db.refresh(course)

        return {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "level": course.level,
            "duration": course.duration,
            "thumbnail": course.thumbnail,
            "status": course.status.value if hasattr(course.status, 'value') else course.status,
            "updated_at": course.updated_at.isoformat() if course.updated_at else None,
        }

    def update_lesson(self, teacher_id: str, course_id: str, lesson_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a lesson within a course with ownership verification."""
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course or str(course.teacher_id) != str(teacher_id):
            raise HTTPException(status_code=403, detail="Course not found or not taught by this teacher")

        lesson = self.db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.course_id == course_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        updatable = {"title", "description", "content", "duration", "duration_text", "status", "video_link", "quizzes_json", "assignments_json"}
        for key, value in data.items():
            if key in updatable and value is not None:
                setattr(lesson, key, value)

        self.db.commit()
        self.db.refresh(lesson)

        return {
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "content": lesson.content,
            "duration": lesson.duration,
            "duration_text": lesson.duration_text,
            "status": lesson.status,
            "video_link": lesson.video_link,
            "quizzes_json": lesson.quizzes_json,
            "assignments_json": lesson.assignments_json,
            "order_index": lesson.order_index,
            "updated_at": lesson.updated_at.isoformat() if lesson.updated_at else None,
        }

    def delete_lesson(self, teacher_id: str, course_id: str, lesson_id: str) -> None:
        """Delete a lesson from a course with ownership verification."""
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course or str(course.teacher_id) != str(teacher_id):
            raise HTTPException(status_code=403, detail="Course not found or not taught by this teacher")

        lesson = self.db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.course_id == course_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        self.db.delete(lesson)
        self.db.commit()


class TeacherStatsService:
    def __init__(self, db: Session):
        """Initialize the teacher stats service with a database session."""
        self.db = db

    def get_dashboard_stats(self, teacher_id: str) -> Dict:
        """Get dashboard statistics for a teacher including students, courses, and grades."""
        # Total distinct students across teacher's courses
        total_students = (
            self.db.query(func.count(distinct(CourseEnrollment.student_id)))
            .join(Course, Course.id == CourseEnrollment.course_id)
            .filter(Course.teacher_id == teacher_id)
            .scalar()
            or 0
        )

        # Active courses
        active_courses = (
            self.db.query(func.count(Course.id))
            .filter(Course.teacher_id == teacher_id, Course.status == "active")
            .scalar()
            or 0
        )

        # Pending submissions (assignments submitted but not graded)
        pending_submissions = (
            self.db.query(func.count(AssignmentSubmission.id))
            .join(Assignment, Assignment.id == AssignmentSubmission.assignment_id)
            .join(Course, Course.id == Assignment.course_id)
            .filter(
                Course.teacher_id == teacher_id,
                AssignmentSubmission.status == AssignmentStatus.SUBMITTED,
            )
            .scalar()
            or 0
        )

        # Calculate class average score
        avg_score = (
            self.db.query(func.avg(Grade.grade))
            .join(Course, Course.id == Grade.course_id)
            .filter(Course.teacher_id == teacher_id)
            .scalar()
            or 0
        )
        class_average = int(avg_score) if avg_score else 0

        # Get all teacher's courses with details
        teacher_courses = self.db.query(Course).filter(
            Course.teacher_id == teacher_id
        ).all()

        classes_data = []
        for course in teacher_courses:
            # Student count
            student_count = (
                self.db.query(func.count(CourseEnrollment.student_id))
                .filter(CourseEnrollment.course_id == course.id)
                .scalar()
                or 0
            )

            # Average score in course
            course_avg = (
                self.db.query(func.avg(Grade.grade))
                .filter(Grade.course_id == course.id)
                .scalar()
                or 0
            )

            # Attendance percentage (mock calculation)
            attendance = 92

            classes_data.append({
                "id": str(course.id),
                "name": course.title,
                "students": student_count,
                "avgScore": int(course_avg) if course_avg else 0,
                "attendance": attendance,
                "status": str(course.status.value) if course.status else "draft"
            })

        # Weekly summary - last 7 days
        week_ago = datetime.now() - timedelta(days=7)

        lessons_taught = (
            self.db.query(func.count(Lesson.id))
            .join(Course, Course.id == Lesson.course_id)
            .filter(
                Course.teacher_id == teacher_id,
                Lesson.created_at >= week_ago
            )
            .scalar()
            or 0
        )

        assignments_given = (
            self.db.query(func.count(Assignment.id))
            .join(Course, Course.id == Assignment.course_id)
            .filter(
                Course.teacher_id == teacher_id,
                Assignment.created_at >= week_ago
            )
            .scalar()
            or 0
        )

        grades_submitted = (
            self.db.query(func.count(Grade.id))
            .join(Course, Course.id == Grade.course_id)
            .filter(
                Course.teacher_id == teacher_id,
                Grade.graded_at >= week_ago
            )
            .scalar()
            or 0
        )

        # Recent assignments
        recent_assignments = (
            self.db.query(Assignment)
            .join(Course, Course.id == Assignment.course_id)
            .filter(Course.teacher_id == teacher_id)
            .order_by(Assignment.created_at.desc())
            .limit(5)
            .all()
        )

        assignments_list = []
        for idx, assignment in enumerate(recent_assignments, 1):
            submitted_count = (
                self.db.query(func.count(AssignmentSubmission.id))
                .filter(AssignmentSubmission.assignment_id == assignment.id)
                .scalar()
                or 0
            )
            student_count = (
                self.db.query(func.count(CourseEnrollment.student_id))
                .filter(CourseEnrollment.course_id == assignment.course_id)
                .scalar()
                or 0
            )
            course = self.db.query(Course).filter(Course.id == assignment.course_id).first()

            assignments_list.append({
                "id": idx,
                "title": assignment.title,
                "class": course.title if course else "Unknown",
                "dueDate": assignment.due_date.strftime("%Y-%m-%d") if assignment.due_date else "",
                "submitted": submitted_count,
                "total": student_count
            })

        # Top performers - students with highest grades
        top_performers = (
            self.db.query(User, Grade)
            .join(Grade, Grade.student_id == User.id)
            .join(Course, Course.id == Grade.course_id)
            .filter(Course.teacher_id == teacher_id)
            .order_by(Grade.grade.desc())
            .limit(5)
            .all()
        )

        performers_list = []
        for idx, (student, grade) in enumerate(top_performers, 1):
            course = self.db.query(Course).filter(Course.id == grade.course_id).first()
            performers_list.append({
                "rank": idx,
                "name": f"{student.first_name} {student.last_name}",
                "score": int(grade.grade) if grade.grade else 0,
                "class": course.title if course else "Unknown",
                "trend": "up"
            })

        # Recent activities - from activity logs
        recent_activities = (
            self.db.query(ActivityLog)
            .order_by(ActivityLog.timestamp.desc())
            .limit(5)
            .all()
        )

        activities_list = []
        for idx, activity in enumerate(recent_activities, 1):
            user = self.db.query(User).filter(User.id == activity.user_id).first()
            time_diff = datetime.now() - activity.timestamp if activity.timestamp else None
            time_str = "recently"
            if time_diff:
                hours = time_diff.total_seconds() / 3600
                if hours < 1:
                    time_str = f"{int(time_diff.total_seconds() / 60)} minutes ago"
                elif hours < 24:
                    time_str = f"{int(hours)} hours ago"
                else:
                    days = time_diff.days
                    time_str = f"{days} days ago"

            activities_list.append({
                "id": idx,
                "user": f"{user.first_name} {user.last_name}" if user else "Unknown",
                "action": activity.action,
                "time": time_str
            })

        return {
            "stats": {
                "total_students": total_students,
                "total_students_change": {"value": 8, "trend": "up"},
                "active_classes": active_courses,
                "active_classes_change": {"value": 1, "trend": "up"},
                "pending_submissions": pending_submissions,
                "pending_submissions_change": {"value": 5, "trend": "down"},
                "class_average": class_average,
                "class_average_change": {"value": 2, "trend": "up"}
            },
            "classes": classes_data,
            "weekly_summary": {
                "lessons_taught": lessons_taught,
                "assignments_given": assignments_given,
                "grades_submitted": grades_submitted
            },
            "recent_assignments": assignments_list,
            "top_performers": performers_list,
            "recent_activities": activities_list
        }

    def capture_snapshot(self, teacher_id: str) -> Dict:
        """Compute and upsert today's snapshot for the teacher, and record timeseries."""
        stats = self.get_dashboard_stats(teacher_id)

        today = date.today()

        # Enrollments today
        enrollments_today = (
            self.db.query(func.count(CourseEnrollment.id))
            .join(Course, Course.id == CourseEnrollment.course_id)
            .filter(
                Course.teacher_id == teacher_id,
                func.date(CourseEnrollment.enrollment_date) == today,
            )
            .scalar()
            or 0
        )

        # Assignment submissions today
        submissions_today = (
            self.db.query(func.count(AssignmentSubmission.id))
            .join(Assignment, Assignment.id == AssignmentSubmission.assignment_id)
            .join(Course, Course.id == Assignment.course_id)
            .filter(
                Course.teacher_id == teacher_id,
                func.date(AssignmentSubmission.submitted_at) == today,
            )
            .scalar()
            or 0
        )

        # Upcoming classes (calendar events starting from now for this teacher's courses)
        upcoming_classes = (
            self.db.query(func.count(CalendarEvent.id))
            .join(Course, Course.id == CalendarEvent.course_id)
            .filter(
                Course.teacher_id == teacher_id,
                CalendarEvent.start_time >= datetime.now(),
            )
            .scalar()
            or 0
        )

        # Upsert snapshot row for today
        snapshot: Optional[TeacherStats] = (
            self.db.query(TeacherStats)
            .filter(
                TeacherStats.teacher_id == teacher_id,
                TeacherStats.snapshot_date == today,
            )
            .one_or_none()
        )

        if snapshot is None:
            snapshot = TeacherStats(
                teacher_id=teacher_id,
                snapshot_date=today,
            )
            self.db.add(snapshot)

        # Use the correct snake_case keys from get_dashboard_stats()
        inner = stats["stats"]
        snapshot.total_courses = inner["active_classes"]
        snapshot.total_students = inner["total_students"]
        snapshot.pending_grading = inner["pending_submissions"]
        snapshot.upcoming_classes = int(upcoming_classes)
        snapshot.enrollments_today = int(enrollments_today)
        snapshot.assignments_submitted_today = int(submissions_today)

        # Commit snapshot
        self.db.commit()
        self.db.refresh(snapshot)

        # Record timeseries points for quick charts (enrollments, submissions)
        now_ts = datetime.now(timezone.utc)
        self.db.add_all([
            TeacherStatTimeseries(
                teacher_id=teacher_id,
                metric_name="enrollments",
                metric_value=float(enrollments_today),
                timestamp=now_ts,
            ),
            TeacherStatTimeseries(
                teacher_id=teacher_id,
                metric_name="submissions",
                metric_value=float(submissions_today),
                timestamp=now_ts,
            ),
        ])
        self.db.commit()

        return {
            "snapshotDate": str(today),
            "totalCourses": snapshot.total_courses,
            "totalStudents": snapshot.total_students,
            "pendingGrading": snapshot.pending_grading,
            "upcomingClasses": snapshot.upcoming_classes,
            "enrollmentsToday": snapshot.enrollments_today,
            "submissionsToday": snapshot.assignments_submitted_today,
        }
