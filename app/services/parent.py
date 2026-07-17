"""Service for aggregating parent dashboard statistics and data."""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, distinct
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.user import User
from app.models.calendar_event import ParentChildRelationship
from app.models.course import CourseEnrollment, Course
from app.models.grade import Grade
from app.models.attendance import Attendance, AttendanceStatus
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.notification import Notification
from app.services.performance_service import PerformanceService


class ParentStatsService:
    """Service for retrieving and aggregating parent dashboard data."""

    @staticmethod
    def convert_letter_grade(numeric_grade: float) -> str:
        """Convert numeric grade to letter grade."""
        if numeric_grade >= 90:
            return "A"
        elif numeric_grade >= 80:
            return "B"
        elif numeric_grade >= 70:
            return "C"
        elif numeric_grade >= 60:
            return "D"
        else:
            return "F"

    @staticmethod
    def get_letter_grade_with_modifier(numeric_grade: float) -> str:
        """Convert numeric grade to letter grade with +/- modifiers."""
        if numeric_grade >= 97:
            return "A+"
        elif numeric_grade >= 90:
            return "A"
        elif numeric_grade >= 87:
            return "B+"
        elif numeric_grade >= 80:
            return "B"
        elif numeric_grade >= 77:
            return "C+"
        elif numeric_grade >= 70:
            return "C"
        elif numeric_grade >= 67:
            return "D+"
        elif numeric_grade >= 60:
            return "D"
        else:
            return "F"

    @staticmethod
    def _serialize_performance_data(perf_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw ORM objects from PerformanceService into plain dicts with
        field names matching what the frontend shared components expect.
        """
        from decimal import Decimal

        # Performance Trend: { date: str, score: number }
        perf_trend = []
        for p in perf_data.get("performance_trend", []):
            perf_trend.append({
                "date": str(p.date) if hasattr(p, 'date') else str(p.get('date', '')),
                "score": float(p.score) if hasattr(p, 'score') else float(p.get('score', 0)),
            })

        # Weekly Activity: { day: str, hours: number, assignments: number }
        weekly = []
        for a in perf_data.get("weekly_activity", []):
            weekly.append({
                "day": a.day_of_week if hasattr(a, 'day_of_week') else a.get('day_of_week', ''),
                "hours": float(a.hours_studied) if hasattr(a, 'hours_studied') else float(a.get('hours_studied', 0)),
                "assignments": int(a.assignments_completed) if hasattr(a, 'assignments_completed') else int(a.get('assignments_completed', 0)),
            })

        # Skills: { skill: str, value: number }
        skills = []
        for s in perf_data.get("skills", []):
            skills.append({
                "skill": s.skill_name if hasattr(s, 'skill_name') else s.get('skill_name', ''),
                "value": float(s.skill_value) if hasattr(s, 'skill_value') else float(s.get('skill_value', 0)),
            })

        # Student Level: { grade: str, stream: str, progress: number, academic_year?: str }
        sl_raw = perf_data.get("student_level")
        student_level = None
        if sl_raw:
            student_level = {
                "grade": sl_raw.grade if hasattr(sl_raw, 'grade') else sl_raw.get('grade', ''),
                "stream": sl_raw.stream if hasattr(sl_raw, 'stream') else sl_raw.get('stream', ''),
                "progress": float(sl_raw.overall_progress) if hasattr(sl_raw, 'overall_progress') else float(sl_raw.get('overall_progress', 0)),
                "academic_year": sl_raw.academic_year if hasattr(sl_raw, 'academic_year') else sl_raw.get('academic_year', None),
            }

        # Subject Marks: { subject: str, score: number }
        marks = []
        for m in perf_data.get("subject_marks", []):
            marks.append({
                "subject": m.subject_name if hasattr(m, 'subject_name') else m.get('subject_name', ''),
                "score": float(m.score) if hasattr(m, 'score') else float(m.get('score', 0)),
            })

        # Improvement Areas: { subject: str, reason: str, suggestion: str, priority?: str }
        improvements = []
        for i in perf_data.get("improvement_areas", []):
            raw_priority = i.priority if hasattr(i, 'priority') else i.get('priority', 'medium')
            improvements.append({
                "subject": i.subject_name if hasattr(i, 'subject_name') else i.get('subject_name', ''),
                "reason": i.reason if hasattr(i, 'reason') else i.get('reason', ''),
                "suggestion": i.suggestion if hasattr(i, 'suggestion') else i.get('suggestion', ''),
                "priority": raw_priority.upper() if raw_priority else "MEDIUM",
            })

        return {
            "performance_trend": perf_trend,
            "weekly_activity": weekly,
            "skills": skills,
            "student_level": student_level,
            "subject_marks": marks,
            "improvement_areas": improvements,
        }

    @staticmethod
    def get_dashboard_stats(parent_id: str, db: Session) -> Dict[str, Any]:
        """
        Get parent dashboard statistics including children info, grades, attendance, and notifications.
        
        Args:
            parent_id: The parent user ID
            db: Database session
            
        Returns:
            Dictionary with stats, children, and notifications
        """
        
        # Get all children for this parent
        children_relationships = db.query(ParentChildRelationship).filter(
            ParentChildRelationship.parent_id == parent_id,
            ParentChildRelationship.verified == True
        ).all()
        
        children_ids = [rel.child_id for rel in children_relationships]
        
        if not children_ids:
            return {
                "stats": {
                    "total_children": 0,
                    "total_children_change": {"value": 0, "trend": "neutral"},
                    "average_grade": "N/A",
                    "average_grade_change": {"value": 0, "trend": "neutral"},
                    "average_attendance": 0,
                    "average_attendance_change": {"value": 0, "trend": "neutral"},
                    "unread_messages": 0,
                    "unread_messages_change": {"value": 0, "trend": "neutral"}
                },
                "children": [],
                "recent_notifications": []
            }
        
        # Calculate stats
        total_children = len(children_ids)
        
        # Get latest grades for all children
        latest_grades = db.query(
            func.avg(Grade.grade).label("avg_grade")
        ).filter(
            Grade.student_id.in_(children_ids)
        ).first()
        
        avg_grade = float(latest_grades.avg_grade) if latest_grades.avg_grade else 0
        avg_grade_letter = ParentStatsService.get_letter_grade_with_modifier(avg_grade) if avg_grade > 0 else "N/A"
        
        # Get attendance percentage
        total_attendance_records = db.query(func.count(Attendance.id)).filter(
            Attendance.student_id.in_(children_ids)
        ).scalar()
        
        present_count = db.query(func.count(Attendance.id)).filter(
            Attendance.student_id.in_(children_ids),
            Attendance.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE])
        ).scalar()
        
        avg_attendance = int((present_count / total_attendance_records * 100) if total_attendance_records > 0 else 0)
        
        # Get unread notifications for parent
        unread_messages = db.query(func.count(Notification.id)).filter(
            Notification.user_id == parent_id,
            Notification.is_read == False
        ).scalar()
        
        # Build children data
        children_data = []
        for child_id in children_ids:
            child_user = db.query(User).filter(User.id == child_id).first()
            
            if not child_user:
                continue
            
            # Get child's courses
            child_courses = db.query(CourseEnrollment).filter(
                CourseEnrollment.student_id == child_id
            ).all()
            
            course_ids = [enrollment.course_id for enrollment in child_courses]
            
            # Get child's grades in their courses
            child_grades = db.query(Grade).filter(
                Grade.student_id == child_id,
                Grade.course_id.in_(course_ids) if course_ids else False
            ).all()
            
            if child_grades:
                avg_child_grade = sum(float(g.grade) for g in child_grades) / len(child_grades)
                child_letter_grade = ParentStatsService.get_letter_grade_with_modifier(avg_child_grade)
            else:
                child_letter_grade = "N/A"
            
            # Get child's attendance percentage
            child_attendance_records = db.query(Attendance).filter(
                Attendance.student_id == child_id
            ).all()
            
            if child_attendance_records:
                child_present = sum(1 for a in child_attendance_records 
                                   if a.status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE])
                child_attendance = int((child_present / len(child_attendance_records)) * 100)
            else:
                child_attendance = 0
            
            # Get subjects (courses)
            subjects = []
            for enrollment in child_courses:
                course = enrollment.course
                if course:
                    subjects.append(course.title)
            
            # Get recent activity
            recent_activity = "No recent activity"
            
            # Check recent grade
            recent_grade = db.query(Grade).filter(
                Grade.student_id == child_id
            ).order_by(Grade.graded_at.desc()).first()
            
            if recent_grade:
                recent_activity = f"Scored {recent_grade.grade}% on {recent_grade.item_type.value}"
            
            # Check recent submission
            if not recent_grade:
                recent_submission = db.query(AssignmentSubmission).filter(
                    AssignmentSubmission.student_id == child_id
                ).order_by(AssignmentSubmission.submitted_at.desc()).first()
                
                if recent_submission:
                    assignment = recent_submission.assignment
                    if assignment:
                        recent_activity = f"Submitted {assignment.title}"
            
            # Compute trend (compare most recent grade vs older average)
            trend = "stable"
            if child_grades:
                sorted_grades = sorted(child_grades, key=lambda g: g.graded_at, reverse=True)
                if len(sorted_grades) >= 2:
                    recent = float(sorted_grades[0].grade)
                    older = sum(float(g.grade) for g in sorted_grades[1:]) / len(sorted_grades[1:])
                    if recent > older + 2:
                        trend = "up"
                    elif recent < older - 2:
                        trend = "down"

            # Get full performance dashboard data for this child
            perf_service = PerformanceService(db)
            child_perf = perf_service.get_complete_dashboard_data(child_id, days=30)
            serialized_perf = ParentStatsService._serialize_performance_data(child_perf)

            children_data.append({
                "id": child_id,
                "name": child_user.full_name,
                "grade": child_letter_grade,
                "attendance": child_attendance,
                "subjects": subjects,
                "recent_activity": recent_activity,
                "avgScore": int(avg_child_grade) if child_grades else None,
                "trend": trend,
                "performance_trend": serialized_perf["performance_trend"],
                "weekly_activity": serialized_perf["weekly_activity"],
                "skills": serialized_perf["skills"],
                "student_level": serialized_perf["student_level"],
                "subject_marks": serialized_perf["subject_marks"],
                "improvement_areas": serialized_perf["improvement_areas"],
            })
        
        # Get recent notifications
        notifications = db.query(Notification).filter(
            Notification.user_id == parent_id
        ).order_by(Notification.created_at.desc()).limit(5).all()
        
        notification_type_mapping = {
            "assignment": "assignment",
            "message": "general",
            "grade": "grade",
            "announcement": "general",
            "reminder": "meeting"
        }
        
        recent_notifications = []
        for notif in notifications:
            recent_notifications.append({
                "id": notif.id,
                "message": notif.message,
                "date": notif.created_at.strftime("%Y-%m-%d"),
                "type": notification_type_mapping.get(notif.type.value if notif.type else "general", "general")
            })
        
        # Calculate trends (mock data - in production would compare with previous periods)
        stats = {
            "total_children": total_children,
            "total_children_change": {
                "value": 0,
                "trend": "neutral"
            },
            "average_grade": avg_grade_letter,
            "average_grade_change": {
                "value": 2,
                "trend": "up"
            },
            "average_attendance": avg_attendance,
            "average_attendance_change": {
                "value": 3,
                "trend": "up"
            },
            "unread_messages": unread_messages,
            "unread_messages_change": {
                "value": 1 if unread_messages > 0 else 0,
                "trend": "down" if unread_messages > 0 else "neutral"
            }
        }
        
        return {
            "stats": stats,
            "children": children_data,
            "recent_notifications": recent_notifications
        }

    @staticmethod
    def get_child_grades(child_id: str, db: Session) -> Dict[str, Any]:
        """
        Get detailed grades information for a specific child.
        
        Args:
            child_id: The child/student user ID
            db: Database session
            
        Returns:
            Dictionary with child info, grades by subject, assignments, and feedback
        """
        
        # Get child user
        child_user = db.query(User).filter(User.id == child_id).first()
        
        if not child_user:
            return {
                "child": None,
                "grades_by_subject": [],
                "recent_assignments": [],
                "teacher_feedback": []
            }
        
        # Get child's course enrollments
        enrollments = db.query(CourseEnrollment).filter(
            CourseEnrollment.student_id == child_id
        ).all()
        
        course_ids = [enrollment.course_id for enrollment in enrollments]
        
        if not course_ids:
            return {
                "child": {
                    "id": child_id,
                    "name": child_user.full_name,
                    "grade_level": "N/A"
                },
                "grades_by_subject": [],
                "recent_assignments": [],
                "teacher_feedback": []
            }
        
        # Get all grades for this student in their courses
        grades = db.query(Grade).filter(
            Grade.student_id == child_id,
            Grade.course_id.in_(course_ids)
        ).all()
        
        # Group grades by course (subject)
        grades_by_course = {}
        for grade in grades:
            if grade.course_id not in grades_by_course:
                grades_by_course[grade.course_id] = []
            grades_by_course[grade.course_id].append(grade)
        
        # Build grades by subject
        grades_by_subject = []
        for course_id in course_ids:
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                continue
            
            # Get grades for this course
            course_grades = grades_by_course.get(course_id, [])
            
            if course_grades:
                avg_grade = sum(float(g.grade) for g in course_grades) / len(course_grades)
                letter_grade = ParentStatsService.get_letter_grade_with_modifier(avg_grade)
                
                # Calculate trend (compare recent vs older grades)
                recent_grades = sorted(course_grades, key=lambda x: x.graded_at, reverse=True)
                trend = "stable"
                if len(recent_grades) >= 2:
                    recent_avg = float(recent_grades[0].grade)
                    older_avg = sum(float(g.grade) for g in recent_grades[1:]) / len(recent_grades[1:]) if len(recent_grades) > 1 else recent_avg
                    if recent_avg > older_avg + 2:
                        trend = "up"
                    elif recent_avg < older_avg - 2:
                        trend = "down"
                
                # Get teacher name
                teacher = db.query(User).filter(User.id == course.teacher_id).first()
                teacher_name = teacher.full_name if teacher else "Unknown"
                
                grades_by_subject.append({
                    "subject": course.title,
                    "grade": letter_grade,
                    "percentage": int(avg_grade),
                    "trend": trend,
                    "teacher": teacher_name
                })
        
        # Get recent assignments with scores
        recent_assignments = []
        for course_id in course_ids:
            assignments = db.query(Assignment).filter(
                Assignment.course_id == course_id
            ).order_by(Assignment.due_date.desc()).limit(10).all()
            
            for assignment in assignments:
                submissions = db.query(AssignmentSubmission).filter(
                    AssignmentSubmission.assignment_id == assignment.id,
                    AssignmentSubmission.student_id == child_id
                ).first()
                
                if submissions and submissions.grade:
                    course = db.query(Course).filter(Course.id == course_id).first()
                    recent_assignments.append({
                        "id": assignment.id,
                        "title": assignment.title,
                        "subject": course.title if course else "Unknown",
                        "score": int(float(submissions.grade)),
                        "date": submissions.submitted_at.strftime("%Y-%m-%d")
                    })
        
        # Sort by date descending and limit to 5
        recent_assignments = sorted(recent_assignments, key=lambda x: x["date"], reverse=True)[:5]
        
        # Get teacher feedback from assignment submissions
        teacher_feedback = []
        feedback_seen = set()
        
        for course_id in course_ids:
            assignments = db.query(Assignment).filter(
                Assignment.course_id == course_id
            ).all()
            
            for assignment in assignments:
                submission = db.query(AssignmentSubmission).filter(
                    AssignmentSubmission.assignment_id == assignment.id,
                    AssignmentSubmission.student_id == child_id,
                    AssignmentSubmission.feedback != None
                ).first()
                
                if submission and submission.feedback:
                    course = db.query(Course).filter(Course.id == course_id).first()
                    teacher = db.query(User).filter(User.id == course.teacher_id).first() if course else None
                    
                    # Avoid duplicates
                    feedback_key = (teacher.id if teacher else "unknown", submission.feedback)
                    if feedback_key not in feedback_seen:
                        feedback_seen.add(feedback_key)
                        
                        # Determine sentiment based on feedback content
                        feedback_lower = submission.feedback.lower()
                        if any(word in feedback_lower for word in ["excellent", "great", "well done", "good", "strong"]):
                            sentiment = "positive"
                        elif any(word in feedback_lower for word in ["improve", "needs", "work on", "attention", "better"]):
                            sentiment = "needs_improvement"
                        else:
                            sentiment = "neutral"
                        
                        teacher_feedback.append({
                            "id": len(teacher_feedback) + 1,
                            "teacher_name": teacher.full_name if teacher else "Unknown",
                            "subject": course.title if course else "Unknown",
                            "feedback": submission.feedback,
                            "sentiment": sentiment,
                            "date": submission.submitted_at.strftime("%Y-%m-%d")
                        })
        
        # Sort feedback by date descending and limit to 5
        teacher_feedback = sorted(teacher_feedback, key=lambda x: x["date"], reverse=True)[:5]
        
        return {
            "child": {
                "id": child_id,
                "name": child_user.full_name,
                "grade_level": "10A"  # Could be derived from student level if stored
            },
            "grades_by_subject": grades_by_subject,
            "recent_assignments": recent_assignments,
            "teacher_feedback": teacher_feedback
        }
