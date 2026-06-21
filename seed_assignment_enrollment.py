"""Seed script: populates assignment_enrollment with dummy data."""
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.assignment import Assignment, AssignmentEnrollment
from app.models.course import CourseEnrollment
from sqlalchemy import text

db = SessionLocal()
now = datetime.utcnow()

students = [
    "student-001",
    "student-003",
    "student-004",
    "student-005",
]

courses_with_assignments = [
    ("course-001", "Introduction to Python Programming", [
        ("Python Basics Quiz", now + timedelta(days=5), 100),
        ("Control Flow Assignment", now + timedelta(days=12), 80),
        ("Final Project Proposal", now - timedelta(days=2), 50),
    ]),
    ("course-002", "Advanced Web Development", [
        ("REST API Design", now + timedelta(days=7), 100),
        ("Frontend Component Library", now - timedelta(days=3), 80),
    ]),
    ("course-003", "Mathematics Grade 10", [
        ("Algebra Problem Set", now + timedelta(days=10), 100),
        ("Geometry Worksheet", now - timedelta(days=5), 60),
        ("Statistics Project", now - timedelta(days=15), 80),
    ]),
    ("course-004", "Physics Fundamentals", [
        ("Newton's Laws Lab Report", now + timedelta(days=8), 100),
        ("Kinematics Quiz", now - timedelta(days=1), 70),
    ]),
    ("course-005", "English Literature", [
        ("Shakespeare Essay", now + timedelta(days=14), 100),
        ("Poetry Analysis", now - timedelta(days=7), 80),
    ]),
]

try:
    for course_id, course_title, assignments in courses_with_assignments:
        for title, due_date, points in assignments:
            existing = db.query(Assignment).filter(
                Assignment.course_id == course_id,
                Assignment.title == title
            ).first()
            if not existing:
                assignment = Assignment(
                    course_id=course_id,
                    title=title,
                    description=f"Complete the {title.lower()} assignment",
                    due_date=due_date,
                    points=points,
                )
                db.add(assignment)
                db.flush()
    db.commit()
    print("Assignments created.")

    for student_id in students:
        for course_id, _, assignments_list in courses_with_assignments:
            enrollment = db.query(CourseEnrollment).filter(
                CourseEnrollment.student_id == student_id,
                CourseEnrollment.course_id == course_id
            ).first()
            if not enrollment:
                enrollment = CourseEnrollment(
                    student_id=student_id,
                    course_id=course_id,
                    enrollment_date=now - timedelta(days=30),
                    status="ACTIVE",
                    progress=0.0,
                )
                db.add(enrollment)
                db.flush()
    db.commit()
    print("Course enrollments created.")

    statuses = ["pending", "submitted", "graded"]
    import random
    random.seed(42)

    count = 0
    for student_id in students:
        for course_id, _, assignments_list in courses_with_assignments:
            assignments_in_course = db.query(Assignment).filter(
                Assignment.course_id == course_id
            ).all()

            for assignment in assignments_in_course:
                existing = db.query(AssignmentEnrollment).filter(
                    AssignmentEnrollment.student_id == student_id,
                    AssignmentEnrollment.assignment_id == assignment.id
                ).first()
                if existing:
                    continue

                status = random.choice(statuses)
                marks = None
                if status == "graded":
                    marks = random.randint(50, 100)

                ae = AssignmentEnrollment(
                    course_id=course_id,
                    student_id=student_id,
                    marks=marks,
                    status=status,
                    assignment_id=assignment.id,
                )
                db.add(ae)
                count += 1

    db.commit()
    print(f"{count} assignment_enrollment records inserted.")

except Exception as e:
    db.rollback()
    print(f"Error: {e}")
    raise
finally:
    db.close()
