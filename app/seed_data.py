"""Seed sample data for student performance dashboard."""

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


def seed_database():
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(User).filter(
            User.email == "alice.williams@student.retinify.com"
        ).first()
        if existing:
            print("Seed data already exists, skipping.")
            return

        student = User(
            id=str(uuid.uuid4()),
            email="alice.williams@student.retinify.com",
            password_hash=bcrypt.hash("Password123"),
            first_name="Alice",
            last_name="Williams",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
        )
        db.add(student)
        db.flush()

        level = StudentLevel(
            id=str(uuid.uuid4()),
            student_id=student.id,
            grade="10A",
            stream="Science",
            overall_progress=Decimal("78.00"),
            academic_year="2025-2026",
        )
        db.add(level)

        base_score = 72
        for i in range(30):
            d = date.today() - timedelta(days=29 - i)
            score = min(100, base_score + i + (i % 5) - (i % 3))
            db.add(
                PerformanceTrend(
                    id=str(uuid.uuid4()),
                    student_id=student.id,
                    date=d,
                    score=Decimal(str(score)),
                )
            )

        activities = [
            ("Mon", 3.5, 2),
            ("Tue", 4.2, 3),
            ("Wed", 3.8, 2),
            ("Thu", 5.1, 4),
            ("Fri", 4.5, 3),
            ("Sat", 6.2, 5),
            ("Sun", 2.8, 1),
        ]
        for i, (day, hours, assignments) in enumerate(activities):
            d = date.today() - timedelta(days=6 - i)
            db.add(
                WeeklyActivity(
                    id=str(uuid.uuid4()),
                    student_id=student.id,
                    date=d,
                    day_of_week=day,
                    hours_studied=Decimal(str(hours)),
                    assignments_completed=assignments,
                    quizzes_completed=assignments,
                    lessons_viewed=assignments + 1,
                )
            )

        skills = [
            ("Problem Solving", 92),
            ("Communication", 88),
            ("Critical Thinking", 95),
            ("Time Management", 85),
            ("Collaboration", 90),
        ]
        for name, value in skills:
            db.add(
                StudentSkill(
                    id=str(uuid.uuid4()),
                    student_id=student.id,
                    skill_name=name,
                    skill_value=Decimal(str(value)),
                    last_assessed=date.today(),
                )
            )

        marks_data = [
            ("Mathematics", 95),
            ("Physics", 92),
            ("Chemistry", 88),
            ("English", 90),
            ("History", 85),
            ("Computer Science", 97),
        ]
        for subj, score in marks_data:
            db.add(
                SubjectMark(
                    id=str(uuid.uuid4()),
                    student_id=student.id,
                    subject_name=subj,
                    score=Decimal(str(score)),
                    max_score=Decimal("100"),
                    assessment_type="Exam",
                    assessment_date=date.today(),
                )
            )

        improvements = [
            (
                "Chemistry",
                "Inconsistent performance in organic chemistry sections",
                "Focus on molecular structure diagrams and reaction mechanisms. Try solving past papers to build confidence.",
                "high",
            ),
            (
                "History",
                "Need stronger analytical skills in essay writing",
                "Practice writing structured essays with clear thesis statements. Review teacher feedback on previous assignments.",
                "medium",
            ),
        ]
        for subj, reason, suggestion, priority in improvements:
            db.add(
                ImprovementArea(
                    id=str(uuid.uuid4()),
                    student_id=student.id,
                    subject_name=subj,
                    reason=reason,
                    suggestion=suggestion,
                    priority=priority,
                    status="active",
                    identified_date=date.today(),
                )
            )

        db.commit()
        print("Seed data created successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
