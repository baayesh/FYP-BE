from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import Optional, List
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
import logging

from app.models.quiz import QuizAttempt
from app.models.grade import Grade, GradeItemType
from app.models.student_lesson import StudentLesson
from app.models.student_performance import PerformanceTrend, SubjectMark, WeeklyActivity, StudentSkill, StudentLevel, ImprovementArea
from app.models.user import User, UserRole
from app.models.course import Course
from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError, ConflictError

logger = logging.getLogger(__name__)


class PerformanceService:
    # use created database connection
    def __init__(self, db: Session):
        self.db = db

    #compute overall score based on quizzes, grades, lessons, and subject marks
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
        """Compute and upsert today's overall performance trend for a student."""
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

    #update weekly_activity table with increments for a student on the current date
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
        """Compute and upsert a subject mark for a student based on grades and quizzes."""
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
        """Backfill performance trends for one or all students from historical data."""
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
        """Helper: compute the overall performance score for a student up to a given date."""
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

    def get_complete_dashboard_data(self, student_id: str, days: int = 30) -> dict:
        """Get all dashboard data for a student including trends, activities, skills, and marks."""
        cutoff_date = date.today() - timedelta(days=days)
        week_ago = date.today() - timedelta(days=7)

        return {
            "performance_trend": self.db.query(PerformanceTrend).filter(
                PerformanceTrend.student_id == student_id,
                PerformanceTrend.date >= cutoff_date
            ).order_by(PerformanceTrend.date).all(),

            "weekly_activity": self.db.query(WeeklyActivity).filter(
                WeeklyActivity.student_id == student_id,
                WeeklyActivity.date >= week_ago
            ).order_by(WeeklyActivity.date).all(),

            "skills": self.db.query(StudentSkill).filter(
                StudentSkill.student_id == student_id
            ).all(),

            "student_level": self.db.query(StudentLevel).filter(
                StudentLevel.student_id == student_id
            ).first(),

            "subject_marks": self._get_latest_subject_marks(student_id),

            "improvement_areas": self.db.query(ImprovementArea).filter(
                ImprovementArea.student_id == student_id,
                ImprovementArea.status == "active"
            ).order_by(
                ImprovementArea.priority.desc(),
                ImprovementArea.identified_date
            ).all()
        }

    def _get_latest_subject_marks(self, student_id: str) -> list:
        """Get subject marks based on graded work, grouped by course (same source as Grades page)."""
        results = (
            self.db.query(
                Course.id,
                Course.title,
                func.avg(Grade.grade),
                func.max(Grade.graded_at)
            )
            .join(Course, Grade.course_id == Course.id)
            .filter(Grade.student_id == student_id, Grade.grade.isnot(None))
            .group_by(Course.id, Course.title)
            .all()
        )

        marks = []
        for course_id, course_title, avg_grade, latest_grade_date in results:
            score = float(avg_grade) if avg_grade else 0
            assessment_date = latest_grade_date.date() if latest_grade_date else date.today()

            marks.append({
                "id": str(uuid4()),
                "student_id": student_id,
                "subject_name": course_title,
                "score": Decimal(str(round(score, 2))),
                "max_score": Decimal("100"),
                "assessment_type": "Overall",
                "assessment_date": assessment_date,
                "course_id": course_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })

        return marks

    def get_performance_trends(self, student_id: str, days: int, course_id: Optional[str] = None) -> list:
        """Get performance trend records for a student within a given number of days."""
        cutoff_date = date.today() - timedelta(days=days)
        query = self.db.query(PerformanceTrend).filter(
            PerformanceTrend.student_id == student_id,
            PerformanceTrend.date >= cutoff_date
        )
        if course_id:
            query = query.filter(PerformanceTrend.course_id == course_id)
        return query.order_by(PerformanceTrend.date).all()

    def get_weekly_activities(self, student_id: str, days: int = 7) -> list:
        """Get weekly activity records for a student within a given number of days."""
        cutoff_date = date.today() - timedelta(days=days)
        return self.db.query(WeeklyActivity).filter(
            WeeklyActivity.student_id == student_id,
            WeeklyActivity.date >= cutoff_date
        ).order_by(WeeklyActivity.date).all()

    def get_skills(self, student_id: str, course_id: Optional[str] = None) -> list:
        """Get skill assessments for a student, optionally filtered by course."""
        query = self.db.query(StudentSkill).filter(
            StudentSkill.student_id == student_id
        )
        if course_id:
            query = query.filter(StudentSkill.course_id == course_id)
        return query.all()

    def create_skill(self, data: dict) -> StudentSkill:
        """Create a new skill assessment record."""
        skill = StudentSkill(**data)
        self.db.add(skill)
        try:
            self.db.commit()
            self.db.refresh(skill)
        except Exception:
            self.db.rollback()
            raise
        return skill

    def update_skill(self, skill_id: str, data: dict) -> StudentSkill:
        """Update an existing skill assessment record by ID."""
        skill = self.db.query(StudentSkill).filter(StudentSkill.id == skill_id).first()
        if not skill:
            raise NotFoundError("Skill assessment not found")
        for key, value in data.items():
            setattr(skill, key, value)
        try:
            self.db.commit()
            self.db.refresh(skill)
        except Exception:
            self.db.rollback()
            raise
        return skill

    def get_level(self, student_id: str) -> Optional[StudentLevel]:
        """Get the current level record for a student."""
        return self.db.query(StudentLevel).filter(
            StudentLevel.student_id == student_id
        ).first()

    def create_level(self, data: dict) -> StudentLevel:
        """Create a new student level record, raising ConflictError if one already exists."""
        existing = self.db.query(StudentLevel).filter(
            StudentLevel.student_id == data["student_id"]
        ).first()
        if existing:
            raise ConflictError("Student level already exists. Use PUT to update.")
        level = StudentLevel(**data)
        self.db.add(level)
        try:
            self.db.commit()
            self.db.refresh(level)
        except Exception:
            self.db.rollback()
            raise
        return level

    def update_level(self, student_id: str, data: dict) -> StudentLevel:
        """Update an existing student level record by student ID."""
        level = self.db.query(StudentLevel).filter(
            StudentLevel.student_id == student_id
        ).first()
        if not level:
            raise NotFoundError("Student level not found. Use POST to create.")
        for key, value in data.items():
            setattr(level, key, value)
        try:
            self.db.commit()
            self.db.refresh(level)
        except Exception:
            self.db.rollback()
            raise
        return level

    def get_subject_marks(self, student_id: str, subject_name: Optional[str] = None,
                          assessment_type: Optional[str] = None, days: int = 90) -> list:
        """Get subject marks for a student with optional filters for subject, type, and date range."""
        cutoff_date = date.today() - timedelta(days=days)
        query = self.db.query(SubjectMark).filter(
            SubjectMark.student_id == student_id,
            SubjectMark.assessment_date >= cutoff_date
        )
        if subject_name:
            query = query.filter(SubjectMark.subject_name == subject_name)
        if assessment_type:
            query = query.filter(SubjectMark.assessment_type == assessment_type)
        return query.order_by(desc(SubjectMark.assessment_date)).all()

    def create_subject_mark(self, data: dict) -> SubjectMark:
        """Create a new subject mark record and update the performance trend."""
        mark = SubjectMark(**data)
        self.db.add(mark)
        try:
            self.db.commit()
            self.db.refresh(mark)
        except Exception:
            self.db.rollback()
            raise

        try:
            self.update_trend(data["student_id"])
        except Exception:
            pass

        return mark

    def get_improvement_areas(self, student_id: str, status_filter: Optional[str] = None,
                              priority: Optional[str] = None) -> list:
        """Get improvement areas for a student, optionally filtered by status and priority."""
        query = self.db.query(ImprovementArea).filter(
            ImprovementArea.student_id == student_id
        )
        if status_filter:
            query = query.filter(ImprovementArea.status == status_filter)
        if priority:
            query = query.filter(ImprovementArea.priority == priority)
        return query.order_by(
            ImprovementArea.priority.desc(),
            ImprovementArea.identified_date
        ).all()

    def create_improvement_area(self, data: dict) -> ImprovementArea:
        """Create a new improvement area record."""
        improvement = ImprovementArea(**data)
        self.db.add(improvement)
        try:
            self.db.commit()
            self.db.refresh(improvement)
        except Exception:
            self.db.rollback()
            raise
        return improvement

    def update_improvement_area(self, improvement_id: str, data: dict) -> ImprovementArea:
        """Update an existing improvement area record by ID."""
        improvement = self.db.query(ImprovementArea).filter(
            ImprovementArea.id == improvement_id
        ).first()
        if not improvement:
            raise NotFoundError("Improvement area not found")
        for key, value in data.items():
            setattr(improvement, key, value)
        try:
            self.db.commit()
            self.db.refresh(improvement)
        except Exception:
            self.db.rollback()
            raise
        return improvement

    def delete_improvement_area(self, improvement_id: str) -> None:
        """Delete an improvement area record by ID."""
        improvement = self.db.query(ImprovementArea).filter(
            ImprovementArea.id == improvement_id
        ).first()
        if not improvement:
            raise NotFoundError("Improvement area not found")
        self.db.delete(improvement)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def get_analytics_summary(self, student_id: str) -> dict:
        """Get a summary of analytics for a student including performance, hours, and skills."""
        thirty_days_ago = date.today() - timedelta(days=30)
        week_ago = date.today() - timedelta(days=7)

        avg_performance = self.db.query(func.avg(PerformanceTrend.score)).filter(
            PerformanceTrend.student_id == student_id,
            PerformanceTrend.date >= thirty_days_ago
        ).scalar() or 0

        total_hours = self.db.query(func.sum(WeeklyActivity.hours_studied)).filter(
            WeeklyActivity.student_id == student_id,
            WeeklyActivity.date >= week_ago
        ).scalar() or 0

        total_assignments = self.db.query(func.sum(WeeklyActivity.assignments_completed)).filter(
            WeeklyActivity.student_id == student_id,
            WeeklyActivity.date >= week_ago
        ).scalar() or 0

        avg_skill = self.db.query(func.avg(StudentSkill.skill_value)).filter(
            StudentSkill.student_id == student_id
        ).scalar() or 0

        active_improvements = self.db.query(func.count(ImprovementArea.id)).filter(
            ImprovementArea.student_id == student_id,
            ImprovementArea.status == "active"
        ).scalar() or 0

        return {
            "average_performance": float(avg_performance),
            "total_study_hours_week": float(total_hours),
            "total_assignments_week": int(total_assignments),
            "average_skill_level": float(avg_skill),
            "active_improvement_areas": int(active_improvements)
        }

    def create_performance_trend(self, data: dict) -> PerformanceTrend:
        """Create a new performance trend record."""
        trend = PerformanceTrend(**data)
        self.db.add(trend)
        try:
            self.db.commit()
            self.db.refresh(trend)
        except Exception:
            self.db.rollback()
            raise
        return trend

    def create_weekly_activity(self, data: dict) -> WeeklyActivity:
        """Create a new weekly activity record."""
        activity = WeeklyActivity(**data)
        self.db.add(activity)
        try:
            self.db.commit()
            self.db.refresh(activity)
        except Exception:
            self.db.rollback()
            raise
        return activity
