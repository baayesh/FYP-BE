from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.models.quiz import QuizAttempt
from app.models.grade import Grade, GradeItemType
from app.models.student_lesson import StudentLesson
from app.models.student_performance import PerformanceTrend, SubjectMark, WeeklyActivity
from app.models.user import User, UserRole
from app.models.course import Course
from app.core.config import settings


class PerformanceService:
    def __init__(self, db: Session):
        self.db = db

    def compute_overall_score(self, student_id: str) -> Decimal:
        all_scores: List[float] = []
        cutoff = datetime.utcnow() - timedelta(days=settings.PERFORMANCE_TREND_LOOKBACK_DAYS)
        cutoff_date = date.today() - timedelta(days=settings.PERFORMANCE_TREND_LOOKBACK_DAYS)

        quiz_scores = self.db.query(QuizAttempt.score).filter(
            QuizAttempt.student_id == student_id,
            QuizAttempt.score.isnot(None),
            QuizAttempt.submitted_at >= cutoff
        ).all()
        for (score,) in quiz_scores:
            all_scores.append(float(score))

        grades = self.db.query(Grade.grade).filter(
            Grade.student_id == student_id,
            Grade.grade.isnot(None),
            Grade.graded_at >= cutoff
        ).all()
        for (grade,) in grades:
            all_scores.append(float(grade))

        lessons = self.db.query(
            StudentLesson.Q1_Result, StudentLesson.Q2_Result,
            StudentLesson.Q3_Result, StudentLesson.Q4_Result,
        ).filter(
            StudentLesson.student_id == student_id
        ).all()
        for lesson in lessons:
            for result in [lesson.Q1_Result, lesson.Q2_Result, lesson.Q3_Result, lesson.Q4_Result]:
                if result is not None:
                    all_scores.append(float(result) * 10)

        subject_marks = self.db.query(SubjectMark.score, SubjectMark.max_score).filter(
            SubjectMark.student_id == student_id,
            SubjectMark.assessment_date >= cutoff_date
        ).all()
        for score, max_score in subject_marks:
            max_val = float(max_score) if max_score else 100.0
            if max_val > 0:
                all_scores.append(float(score) / max_val * 100)

        if not all_scores:
            return Decimal("0")

        avg = sum(all_scores) / len(all_scores)
        return Decimal(str(round(avg, 2)))

    def update_trend(self, student_id: str) -> PerformanceTrend:
        overall = self.compute_overall_score(student_id)

        trend = self.db.query(PerformanceTrend).filter(
            PerformanceTrend.student_id == student_id,
            PerformanceTrend.date == date.today()
        ).first()

        if trend:
            trend.score = overall
        else:
            trend = PerformanceTrend(
                student_id=student_id,
                date=date.today(),
                score=overall
            )
            self.db.add(trend)

        try:
            self.db.commit()
            if trend.id is None:
                self.db.refresh(trend)
        except Exception:
            self.db.rollback()
            raise

        return trend

    def log_activity(self, student_id: str, **increments):
        today = date.today()
        day_name = today.strftime("%a")

        activity = self.db.query(WeeklyActivity).filter(
            WeeklyActivity.student_id == student_id,
            WeeklyActivity.date == today
        ).first()

        if not activity:
            activity = WeeklyActivity(
                student_id=student_id,
                date=today,
                day_of_week=day_name
            )
            self.db.add(activity)
            self.db.flush()

        for field, val in increments.items():
            if hasattr(activity, field) and val:
                current = getattr(activity, field) or 0
                setattr(activity, field, current + val)

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def compute_subject_mark(self, student_id: str, subject_name: str, course_id: str = None) -> Optional[SubjectMark]:
        all_scores: List[float] = []

        grades_query = self.db.query(Grade).filter(
            Grade.student_id == student_id,
            Grade.grade.isnot(None)
        )
        if course_id:
            grades_query = grades_query.filter(Grade.course_id == course_id)
        grades = grades_query.all()

        for g in grades:
            max_pts = float(g.points_possible) if g.points_possible else 100.0
            if max_pts > 0:
                pct = (float(g.points_earned) / max_pts * 100) if g.points_earned else float(g.grade)
                all_scores.append(pct)

        quiz_attempts = self.db.query(QuizAttempt).filter(
            QuizAttempt.student_id == student_id,
            QuizAttempt.score.isnot(None)
        ).all()
        for qa in quiz_attempts:
            all_scores.append(float(qa.score))

        if not all_scores:
            return None

        avg = sum(all_scores) / len(all_scores)
        score_val = Decimal(str(round(avg, 2)))

        existing = self.db.query(SubjectMark).filter(
            SubjectMark.student_id == student_id,
            SubjectMark.subject_name == subject_name
        ).first()

        if existing:
            existing.score = score_val
            existing.assessment_date = date.today()
            existing.assessment_type = "auto"
            mark = existing
        else:
            mark = SubjectMark(
                student_id=student_id,
                subject_name=subject_name,
                score=score_val,
                max_score=Decimal("100"),
                assessment_type="auto",
                assessment_date=date.today(),
                course_id=course_id
            )
            self.db.add(mark)

        try:
            self.db.commit()
            if mark.id is None:
                self.db.refresh(mark)
        except Exception:
            self.db.rollback()
            raise

        return mark

    def backfill_trends(self, student_id: Optional[str] = None):
        if student_id:
            student_ids = [student_id]
        else:
            students = self.db.query(User.id).filter(User.role == UserRole.STUDENT).all()
            student_ids = [s[0] for s in students]

        for sid in student_ids:
            dates: set[date] = set()

            quiz_dates = self.db.query(
                func.date(QuizAttempt.submitted_at)
            ).filter(
                QuizAttempt.student_id == sid,
                QuizAttempt.submitted_at.isnot(None)
            ).all()
            for (d,) in quiz_dates:
                if d:
                    dates.add(d)

            grade_dates = self.db.query(
                func.date(Grade.graded_at)
            ).filter(
                Grade.student_id == sid,
                Grade.graded_at.isnot(None)
            ).all()
            for (d,) in grade_dates:
                if d:
                    dates.add(d)

            lesson_dates = self.db.query(
                func.date(StudentLesson.created_at)
            ).filter(
                StudentLesson.student_id == sid,
                StudentLesson.created_at.isnot(None)
            ).all()
            for (d,) in lesson_dates:
                if d:
                    dates.add(d)

            mark_dates = self.db.query(SubjectMark.assessment_date).filter(
                SubjectMark.student_id == sid
            ).all()
            for (d,) in mark_dates:
                if d:
                    dates.add(d)

            for d in sorted(dates):
                overall = self._compute_score_up_to(sid, d)
                existing = self.db.query(PerformanceTrend).filter(
                    PerformanceTrend.student_id == sid,
                    PerformanceTrend.date == d
                ).first()

                if existing:
                    existing.score = overall
                else:
                    self.db.add(PerformanceTrend(
                        student_id=sid,
                        date=d,
                        score=overall
                    ))

            self.db.commit()

    def _compute_score_up_to(self, student_id: str, max_date: date) -> Decimal:
        all_scores: List[float] = []
        max_dt = datetime.combine(max_date, datetime.max.time())

        quiz_scores = self.db.query(QuizAttempt.score).filter(
            QuizAttempt.student_id == student_id,
            QuizAttempt.score.isnot(None),
            QuizAttempt.submitted_at <= max_dt
        ).all()
        for (score,) in quiz_scores:
            all_scores.append(float(score))

        grades = self.db.query(Grade.grade).filter(
            Grade.student_id == student_id,
            Grade.grade.isnot(None),
            Grade.graded_at <= max_dt
        ).all()
        for (grade,) in grades:
            all_scores.append(float(grade))

        lessons = self.db.query(
            StudentLesson.Q1_Result, StudentLesson.Q2_Result,
            StudentLesson.Q3_Result, StudentLesson.Q4_Result,
        ).filter(
            StudentLesson.student_id == student_id,
            StudentLesson.created_at <= max_dt
        ).all()
        for lesson in lessons:
            for r in [lesson.Q1_Result, lesson.Q2_Result, lesson.Q3_Result, lesson.Q4_Result]:
                if r is not None:
                    all_scores.append(float(r) * 10)

        marks = self.db.query(SubjectMark.score, SubjectMark.max_score).filter(
            SubjectMark.student_id == student_id,
            SubjectMark.assessment_date <= max_date
        ).all()
        for score, max_score in marks:
            max_val = float(max_score) if max_score else 100.0
            if max_val > 0:
                all_scores.append(float(score) / max_val * 100)

        if not all_scores:
            return Decimal("0")

        avg = sum(all_scores) / len(all_scores)
        return Decimal(str(round(avg, 2)))
