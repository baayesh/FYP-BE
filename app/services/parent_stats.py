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
                child_letter_grade = ParentStatsService.convert_letter_grade(avg_child_grade)
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
            
            children_data.append({
                "id": child_id,
                "name": child_user.full_name,
                "grade": child_letter_grade,
                "attendance": child_attendance,
                "subjects": subjects,
                "recent_activity": recent_activity
            })
        
        # Get recent notifications
        notifications = db.query(Notification).filter(
            Notification.user_id == parent_id
        ).order_by(Notification.created_at.desc()).limit(5).all()
        
        notification_type_mapping = {
            "assignment": "assignment",
            "message": "general",
            "grade": "achievement",
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

