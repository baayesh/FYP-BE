from datetime import datetime, timezone, date, timedelta
from typing import Dict, Optional, List

from sqlalchemy import func, distinct, and_
from sqlalchemy.orm import Session

from app.models.teacher_stats import TeacherStats, TeacherStatTimeseries
from app.models.course import Course, CourseEnrollment, Lesson
from app.models.assignment import Assignment, AssignmentSubmission, AssignmentStatus
from app.models.calendar_event import CalendarEvent, EventType
from app.models.grade import Grade
from app.models.user import User
from app.models.activity_log import ActivityLog


class TeacherStatsService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_stats(self, teacher_id: str) -> Dict:
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
            total_students = (
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
                "total": total_students
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

        snapshot.total_courses = stats["totalCourses"]
        snapshot.total_students = stats["totalStudents"]
        snapshot.pending_grading = stats["pendingGrading"]
        snapshot.upcoming_classes = stats["upcomingClasses"]
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
