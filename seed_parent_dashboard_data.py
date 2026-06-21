"""Seed parent dashboard data for testing."""

import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

sys.path.insert(0, '/Volumes/Elements/Projects/FYP/retinify_backend')

from app.core.database import SessionLocal, engine, Base
from app.models.user import User, UserRole, UserStatus
from app.models.calendar_event import ParentChildRelationship
from app.models.course import Course, CourseEnrollment, Lesson, LessonType, CourseStatus, EnrollmentStatus
from app.models.grade import Grade, GradeItemType
from app.models.attendance import Attendance, AttendanceStatus
from app.models.assignment import Assignment, AssignmentSubmission, AssignmentStatus
from app.models.notification import Notification, NotificationType
import uuid
import hashlib


def seed_parent_data():
    """Seed parent, children, and related data for testing."""
    db = SessionLocal()
    
    try:
        # Create parent user
        parent_id = str(uuid.uuid4())
        parent = User(
            id=parent_id,
            email="parent@example.com",
            password_hash=hashlib.sha256("password123".encode()).hexdigest(),
            first_name="John",
            last_name="Johnson",
            role=UserRole.PARENT,
            status=UserStatus.ACTIVE,
            phone="+1234567890"
        )
        db.add(parent)
        
        # Create children
        child1_id = str(uuid.uuid4())
        child1 = User(
            id=child1_id,
            email="alice@example.com",
            password_hash=hashlib.sha256("password123".encode()).hexdigest(),
            first_name="Alice",
            last_name="Johnson",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        db.add(child1)
        
        child2_id = str(uuid.uuid4())
        child2 = User(
            id=child2_id,
            email="bob@example.com",
            password_hash=hashlib.sha256("password123".encode()).hexdigest(),
            first_name="Bob",
            last_name="Johnson",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        db.add(child2)
        
        # Create parent-child relationships
        rel1 = ParentChildRelationship(
            parent_id=parent_id,
            child_id=child1_id,
            relationship_type="parent",
            verified=True
        )
        db.add(rel1)
        
        rel2 = ParentChildRelationship(
            parent_id=parent_id,
            child_id=child2_id,
            relationship_type="parent",
            verified=True
        )
        db.add(rel2)
        
        # Create teacher
        teacher_id = str(uuid.uuid4())
        teacher = User(
            id=teacher_id,
            email="teacher@example.com",
            password_hash=hashlib.sha256("password123".encode()).hexdigest(),
            first_name="Dr.",
            last_name="Smith",
            role=UserRole.TEACHER,
            status=UserStatus.ACTIVE
        )
        db.add(teacher)
        
        # Create courses
        course1_id = str(uuid.uuid4())
        course1 = Course(
            id=course1_id,
            teacher_id=teacher_id,
            title="Mathematics 101",
            description="Introduction to Mathematics",
            category="Mathematics",
            level="Beginner",
            status=CourseStatus.ACTIVE,
            code="MATH101",
            instructor="Dr. Smith"
        )
        db.add(course1)
        
        course2_id = str(uuid.uuid4())
        course2 = Course(
            id=course2_id,
            teacher_id=teacher_id,
            title="Science Fundamentals",
            description="Basic Science Concepts",
            category="Science",
            level="Beginner",
            status=CourseStatus.ACTIVE,
            code="SCI101",
            instructor="Dr. Smith"
        )
        db.add(course2)
        
        course3_id = str(uuid.uuid4())
        course3 = Course(
            id=course3_id,
            teacher_id=teacher_id,
            title="English Literature",
            description="Classic Literature and Writing",
            category="English",
            level="Intermediate",
            status=CourseStatus.ACTIVE,
            code="ENG102",
            instructor="Dr. Smith"
        )
        db.add(course3)
        
        db.flush()
        
        # Enroll children in courses
        # Alice: Math, Science
        enroll1 = CourseEnrollment(
            student_id=child1_id,
            course_id=course1_id,
            status=EnrollmentStatus.ACTIVE,
            progress=75
        )
        db.add(enroll1)
        
        enroll2 = CourseEnrollment(
            student_id=child1_id,
            course_id=course2_id,
            status=EnrollmentStatus.ACTIVE,
            progress=85
        )
        db.add(enroll2)
        
        # Bob: Science, English
        enroll3 = CourseEnrollment(
            student_id=child2_id,
            course_id=course2_id,
            status=EnrollmentStatus.ACTIVE,
            progress=70
        )
        db.add(enroll3)
        
        enroll4 = CourseEnrollment(
            student_id=child2_id,
            course_id=course3_id,
            status=EnrollmentStatus.ACTIVE,
            progress=80
        )
        db.add(enroll4)
        
        db.flush()
        
        # Create assignments
        assignment1_id = str(uuid.uuid4())
        assignment1 = Assignment(
            id=assignment1_id,
            course_id=course1_id,
            title="Algebra Basics",
            description="Practice basic algebra problems",
            due_date=datetime.now() + timedelta(days=7),
            points=100
        )
        db.add(assignment1)
        
        assignment2_id = str(uuid.uuid4())
        assignment2 = Assignment(
            id=assignment2_id,
            course_id=course2_id,
            title="Chemistry Lab Report",
            description="Write a lab report on chemical reactions",
            due_date=datetime.now() + timedelta(days=5),
            points=100
        )
        db.add(assignment2)
        
        db.flush()
        
        # Create grades for Alice (Math: 95, Science: 88)
        grade1 = Grade(
            id=str(uuid.uuid4()),
            student_id=child1_id,
            course_id=course1_id,
            item_type=GradeItemType.QUIZ,
            item_id=str(uuid.uuid4()),
            grade=95,
            points_earned=95,
            points_possible=100,
            letter_grade="A",
            graded_by=teacher_id,
            graded_at=datetime.now() - timedelta(days=2)
        )
        db.add(grade1)
        
        grade2 = Grade(
            id=str(uuid.uuid4()),
            student_id=child1_id,
            course_id=course2_id,
            item_type=GradeItemType.EXAM,
            item_id=str(uuid.uuid4()),
            grade=88,
            points_earned=88,
            points_possible=100,
            letter_grade="B+",
            graded_by=teacher_id,
            graded_at=datetime.now() - timedelta(days=3)
        )
        db.add(grade2)
        
        # Create grades for Bob (Science: 85, English: 92)
        grade3 = Grade(
            id=str(uuid.uuid4()),
            student_id=child2_id,
            course_id=course2_id,
            item_type=GradeItemType.ASSIGNMENT,
            item_id=str(uuid.uuid4()),
            grade=85,
            points_earned=85,
            points_possible=100,
            letter_grade="B",
            graded_by=teacher_id,
            graded_at=datetime.now() - timedelta(days=1)
        )
        db.add(grade3)
        
        grade4 = Grade(
            id=str(uuid.uuid4()),
            student_id=child2_id,
            course_id=course3_id,
            item_type=GradeItemType.ESSAY,
            item_id=str(uuid.uuid4()),
            grade=92,
            points_earned=92,
            points_possible=100,
            letter_grade="A-",
            graded_by=teacher_id,
            graded_at=datetime.now() - timedelta(days=4)
        )
        db.add(grade4)
        
        db.flush()
        
        # Create attendance records
        # Alice: 8 present, 1 absent in last 9 days = ~89%
        for i in range(9):
            attendance = Attendance(
                id=str(uuid.uuid4()),
                course_id=course1_id,
                student_id=child1_id,
                date=datetime.now().date() - timedelta(days=i),
                status=AttendanceStatus.PRESENT if i != 3 else AttendanceStatus.ABSENT,
                marked_by=teacher_id
            )
            db.add(attendance)
        
        # Bob: 8 present, 1 late in last 9 days = ~100%
        for i in range(9):
            attendance = Attendance(
                id=str(uuid.uuid4()),
                course_id=course2_id,
                student_id=child2_id,
                date=datetime.now().date() - timedelta(days=i),
                status=AttendanceStatus.LATE if i == 5 else AttendanceStatus.PRESENT,
                marked_by=teacher_id
            )
            db.add(attendance)
        
        db.flush()
        
        # Create assignments submissions
        submission1 = AssignmentSubmission(
            id=str(uuid.uuid4()),
            assignment_id=assignment1_id,
            student_id=child1_id,
            content="Completed algebra problems set 1",
            submitted_at=datetime.now() - timedelta(days=1),
            status=AssignmentStatus.GRADED,
            grade=95,
            feedback="Great work!"
        )
        db.add(submission1)
        
        submission2 = AssignmentSubmission(
            id=str(uuid.uuid4()),
            assignment_id=assignment2_id,
            student_id=child2_id,
            content="Lab report on chemical reactions",
            submitted_at=datetime.now() - timedelta(days=2),
            status=AssignmentStatus.GRADED,
            grade=88,
            feedback="Well written, good analysis"
        )
        db.add(submission2)
        
        db.flush()
        
        # Create more assignments for better grades display
        assignment3_id = str(uuid.uuid4())
        assignment3 = Assignment(
            id=assignment3_id,
            course_id=course3_id,
            title="English Essay on Literature",
            description="Write an essay analyzing themes in classic literature",
            due_date=datetime.now() + timedelta(days=3),
            points=100
        )
        db.add(assignment3)
        
        assignment4_id = str(uuid.uuid4())
        assignment4 = Assignment(
            id=assignment4_id,
            course_id=course1_id,
            title="Calculus Problem Set",
            description="Complete calculus problems from chapters 3-5",
            due_date=datetime.now() + timedelta(days=2),
            points=100
        )
        db.add(assignment4)
        
        assignment5_id = str(uuid.uuid4())
        assignment5 = Assignment(
            id=assignment5_id,
            course_id=course2_id,
            title="Biology Lab Report",
            description="Lab report on cell biology experiments",
            due_date=datetime.now() + timedelta(days=5),
            points=100
        )
        db.add(assignment5)
        
        db.flush()
        
        # Create submissions with feedback
        submission3 = AssignmentSubmission(
            id=str(uuid.uuid4()),
            assignment_id=assignment3_id,
            student_id=child1_id,
            content="Essay on Shakespeare's themes",
            submitted_at=datetime.now() - timedelta(days=5),
            status=AssignmentStatus.GRADED,
            grade=92,
            feedback="Excellent work on recent assignments. Shows strong understanding of literature. Well-structured arguments."
        )
        db.add(submission3)
        
        submission4 = AssignmentSubmission(
            id=str(uuid.uuid4()),
            assignment_id=assignment4_id,
            student_id=child1_id,
            content="Calculus solutions",
            submitted_at=datetime.now() - timedelta(days=3),
            status=AssignmentStatus.GRADED,
            grade=88,
            feedback="Good work. Some minor errors in chain rule application."
        )
        db.add(submission4)
        
        submission5 = AssignmentSubmission(
            id=str(uuid.uuid4()),
            assignment_id=assignment5_id,
            student_id=child2_id,
            content="Lab report on cell division",
            submitted_at=datetime.now() - timedelta(days=4),
            status=AssignmentStatus.GRADED,
            grade=72,
            feedback="Needs to improve attention to detail in lab work. Recommend additional practice with microscope observations."
        )
        db.add(submission5)
        
        # Add more grades for Alice in different subjects
        grade5 = Grade(
            id=str(uuid.uuid4()),
            student_id=child1_id,
            course_id=course3_id,
            item_type=GradeItemType.ESSAY,
            item_id=str(uuid.uuid4()),
            grade=92,
            points_earned=92,
            points_possible=100,
            letter_grade="A-",
            graded_by=teacher_id,
            graded_at=datetime.now() - timedelta(days=5)
        )
        db.add(grade5)
        
        # Add more grades for Bob
        grade6 = Grade(
            id=str(uuid.uuid4()),
            student_id=child2_id,
            course_id=course3_id,
            item_type=GradeItemType.ESSAY,
            item_id=str(uuid.uuid4()),
            grade=88,
            points_earned=88,
            points_possible=100,
            letter_grade="B+",
            graded_by=teacher_id,
            graded_at=datetime.now() - timedelta(days=6)
        )
        db.add(grade6)
        
        db.flush()
        
        # Create notifications for parent
        notif1 = Notification(
            id=str(uuid.uuid4()),
            user_id=parent_id,
            type=NotificationType.GRADE,
            title="Alice scored 95% on Math quiz",
            message="Alice scored 95% on Math quiz",
            is_read=False,
            created_at=datetime.now() - timedelta(days=2)
        )
        db.add(notif1)
        
        notif2 = Notification(
            id=str(uuid.uuid4()),
            user_id=parent_id,
            type=NotificationType.ANNOUNCEMENT,
            title="Parent-teacher meeting",
            message="Bob has a parent-teacher meeting scheduled for tomorrow",
            is_read=False,
            created_at=datetime.now() - timedelta(days=1)
        )
        db.add(notif2)
        
        notif3 = Notification(
            id=str(uuid.uuid4()),
            user_id=parent_id,
            type=NotificationType.ASSIGNMENT,
            title="New assignment posted",
            message="New assignment posted in Science class",
            is_read=False,
            created_at=datetime.now() - timedelta(days=3)
        )
        db.add(notif3)
        
        notif4 = Notification(
            id=str(uuid.uuid4()),
            user_id=parent_id,
            type=NotificationType.GRADE,
            title="Bob scored 92% on English Essay",
            message="Bob scored 92% on English Essay",
            is_read=True,
            created_at=datetime.now() - timedelta(days=4)
        )
        db.add(notif4)
        
        notif5 = Notification(
            id=str(uuid.uuid4()),
            user_id=parent_id,
            type=NotificationType.MESSAGE,
            title="New message from teacher",
            message="Teacher Dr. Smith sent you a message",
            is_read=True,
            created_at=datetime.now() - timedelta(days=5)
        )
        db.add(notif5)
        
        db.commit()
        
        print(f"✅ Parent dashboard test data seeded successfully!")
        print(f"   Parent ID: {parent_id}")
        print(f"   Parent Email: parent@example.com")
        print(f"   Child 1 (Alice): {child1_id}")
        print(f"   Child 2 (Bob): {child2_id}")
        print(f"\n   Test endpoint:")
        print(f"   GET http://localhost:8000/api/v1/parent/dashboard?parent_id={parent_id}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_parent_data()
