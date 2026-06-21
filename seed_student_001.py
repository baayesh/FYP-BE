"""Seed student-001 with dummy dashboard performance data."""
import uuid
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from app.core.database import SessionLocal, init_db
from app.models.user import User, UserRole, UserStatus
from app.models.student_performance import (
    PerformanceTrend,
    WeeklyActivity,
    StudentSkill,
    StudentLevel,
    SubjectMark,
    ImprovementArea,
)


def seed():
    init_db()
    db = SessionLocal()
    try:
        student = db.query(User).filter(User.id == "student-001").first()
        if not student:
            student = User(
                id="student-001",
                email="student-001@student.retinify.com",
                password_hash=bcrypt.hash("Password123"),
                first_name="Demo",
                last_name="Student",
                role=UserRole.STUDENT,
                status=UserStatus.ACTIVE,
            )
            db.add(student)
            db.flush()
            print("Created user: student-001")
        else:
            # Clear existing performance data for this student
            db.query(ImprovementArea).filter(ImprovementArea.student_id == "student-001").delete()
            db.query(SubjectMark).filter(SubjectMark.student_id == "student-001").delete()
            db.query(StudentLevel).filter(StudentLevel.student_id == "student-001").delete()
            db.query(StudentSkill).filter(StudentSkill.student_id == "student-001").delete()
            db.query(WeeklyActivity).filter(WeeklyActivity.student_id == "student-001").delete()
            db.query(PerformanceTrend).filter(PerformanceTrend.student_id == "student-001").delete()
            db.flush()
            print("Cleared existing performance data for student-001")

        # 1. Student Level
        level = StudentLevel(
            id=str(uuid.uuid4()),
            student_id="student-001",
            grade="10A",
            stream="Science",
            overall_progress=Decimal("78.00"),
            academic_year="2025-2026",
        )
        db.add(level)

        # 2. Performance Trend (30 days)
        base_score = 68
        for i in range(30):
            d = date.today() - timedelta(days=29 - i)
            score = min(100, base_score + i + (i % 5) - (i % 3))
            db.add(PerformanceTrend(
                id=str(uuid.uuid4()),
                student_id="student-001",
                date=d,
                score=Decimal(str(score)),
            ))

        # 3. Weekly Activity (7 days)
        activities = [
            ("Mon", 3.5, 2, 2, 3),
            ("Tue", 4.2, 3, 1, 2),
            ("Wed", 3.8, 2, 3, 4),
            ("Thu", 5.1, 4, 2, 3),
            ("Fri", 4.5, 3, 2, 4),
            ("Sat", 6.2, 5, 3, 5),
            ("Sun", 2.8, 1, 1, 2),
        ]
        for i, (day, hours, assignments, quizzes, lessons) in enumerate(activities):
            d = date.today() - timedelta(days=6 - i)
            db.add(WeeklyActivity(
                id=str(uuid.uuid4()),
                student_id="student-001",
                date=d,
                day_of_week=day,
                hours_studied=Decimal(str(hours)),
                assignments_completed=assignments,
                quizzes_completed=quizzes,
                lessons_viewed=lessons,
            ))

        # 4. Student Skills
        skills = [
            ("Problem Solving", 92),
            ("Communication", 88),
            ("Critical Thinking", 95),
            ("Time Management", 85),
            ("Collaboration", 90),
        ]
        for name, value in skills:
            db.add(StudentSkill(
                id=str(uuid.uuid4()),
                student_id="student-001",
                skill_name=name,
                skill_value=Decimal(str(value)),
                last_assessed=date.today(),
            ))

        # 5. Subject Marks (latest per subject)
        marks = [
            ("Mathematics", 95, "Exam"),
            ("Physics", 92, "Exam"),
            ("Chemistry", 88, "Exam"),
            ("English", 90, "Exam"),
            ("History", 85, "Exam"),
            ("Computer Science", 97, "Exam"),
            ("Mathematics", 82, "Quiz"),
            ("Physics", 78, "Quiz"),
            ("English", 91, "Assignment"),
        ]
        for subj, score, atype in marks:
            db.add(SubjectMark(
                id=str(uuid.uuid4()),
                student_id="student-001",
                subject_name=subj,
                score=Decimal(str(score)),
                max_score=Decimal("100"),
                assessment_type=atype,
                assessment_date=date.today() - timedelta(days=marks.index((subj, score, atype)) % 7),
            ))

        # 6. Improvement Areas
        improvements = [
            ("Chemistry", "Inconsistent performance in organic chemistry sections",
             "Focus on molecular structure diagrams and reaction mechanisms. Try solving past papers to build confidence.",
             "high"),
            ("History", "Need stronger analytical skills in essay writing",
             "Practice writing structured essays with clear thesis statements. Review teacher feedback on previous assignments.",
             "medium"),
            ("Physics", "Struggling with electromagnetism concepts",
             "Review Maxwell's equations and practice circuit problems. Use simulation tools for visualization.",
             "high"),
        ]
        for subj, reason, suggestion, priority in improvements:
            db.add(ImprovementArea(
                id=str(uuid.uuid4()),
                student_id="student-001",
                subject_name=subj,
                reason=reason,
                suggestion=suggestion,
                priority=priority,
                status="active",
                identified_date=date.today() - timedelta(days=14),
            ))

        db.commit()
        print("Successfully seeded dashboard data for student-001")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
