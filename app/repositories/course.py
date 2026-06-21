from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from app.models.course import Course, CourseEnrollment, Lesson, LessonProgress, CourseStatus, EnrollmentStatus
from app.models.user import User

class CourseRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, course_data: dict) -> Course:
        """Create a new course"""
        course = Course(**course_data)
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        return course

    def get_by_id(self, course_id: Union[UUID, str]) -> Optional[Course]:
        """Get course by ID with teacher info"""
        return self.db.query(Course).options(
            joinedload(Course.teacher)
        ).filter(Course.id == str(course_id)).first()

    def get_all(self, 
                skip: int = 0, 
                limit: int = 100,
                status: Optional[CourseStatus] = None,
                category: Optional[str] = None,
                teacher_id: Optional[UUID] = None,
                search: Optional[str] = None) -> List[Course]:
        """Get all courses with optional filters"""
        query = self.db.query(Course).options(joinedload(Course.teacher))

        # Apply filters
        if status:
            query = query.filter(Course.status == status)
        
        if category:
            query = query.filter(Course.category == category)
        
        if teacher_id:
            query = query.filter(Course.teacher_id == teacher_id)
        
        if search:
            search_filter = or_(
                Course.title.ilike(f"%{search}%"),
                Course.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        return query.offset(skip).limit(limit).all()

    def get_by_teacher(self, teacher_id: UUID, skip: int = 0, limit: int = 100) -> List[Course]:
        """Get courses by teacher ID"""
        return self.db.query(Course).filter(
            Course.teacher_id == teacher_id
        ).offset(skip).limit(limit).all()

    def get_enrolled_courses(self, student_id: UUID, 
                           status: Optional[EnrollmentStatus] = None,
                           skip: int = 0, 
                           limit: int = 100) -> List[Course]:
        """Get courses enrolled by student"""
        query = self.db.query(Course).join(CourseEnrollment).options(
            joinedload(Course.teacher)
        ).filter(CourseEnrollment.student_id == student_id)
        
        if status:
            query = query.filter(CourseEnrollment.status == status)
        
        return query.offset(skip).limit(limit).all()

    def update(self, course_id: UUID, update_data: dict) -> Optional[Course]:
        """Update course by ID"""
        course = self.get_by_id(course_id)
        if not course:
            return None

        for key, value in update_data.items():
            if hasattr(course, key) and value is not None:
                setattr(course, key, value)
        
        self.db.commit()
        self.db.refresh(course)
        return course

    def delete(self, course_id: UUID) -> bool:
        """Delete course by ID"""
        course = self.get_by_id(course_id)
        if not course:
            return False

        self.db.delete(course)
        self.db.commit()
        return True

    def enroll_student(self, course_id: UUID, student_id: UUID) -> CourseEnrollment:
        """Enroll student in course"""
        enrollment = CourseEnrollment(
            student_id=student_id,
            course_id=course_id,
            status=EnrollmentStatus.ACTIVE
        )
        self.db.add(enrollment)
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment

    def get_enrollment(self, course_id: UUID, student_id: UUID) -> Optional[CourseEnrollment]:
        """Check if student is enrolled in course"""
        return self.db.query(CourseEnrollment).filter(
            and_(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.student_id == student_id
            )
        ).first()

    def get_course_enrollments(self, course_id: UUID) -> List[CourseEnrollment]:
        """Get all enrollments for a course"""
        return self.db.query(CourseEnrollment).options(
            joinedload(CourseEnrollment.student)
        ).filter(CourseEnrollment.course_id == course_id).all()

    def count_enrolled_students(self, course_id: UUID) -> int:
        """Count enrolled students in course"""
        return self.db.query(func.count(CourseEnrollment.id)).filter(
            and_(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.status == EnrollmentStatus.ACTIVE
            )
        ).scalar()

class LessonRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, lesson_data: dict) -> Lesson:
        """Create a new lesson"""
        lesson = Lesson(**lesson_data)
        self.db.add(lesson)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    def get_by_id(self, lesson_id: Union[UUID, str]) -> Optional[Lesson]:
        """Get lesson by ID"""
        return self.db.query(Lesson).filter(Lesson.id == str(lesson_id)).first()

    def get_by_course(self, course_id: Union[UUID, str]) -> List[Lesson]:
        """Get all lessons for a course ordered by index"""
        return self.db.query(Lesson).filter(
            Lesson.course_id == str(course_id)
        ).order_by(Lesson.order_index).all()

    def update(self, lesson_id: Union[UUID, str], update_data: dict) -> Optional[Lesson]:
        """Update a lesson"""
        lesson = self.get_by_id(lesson_id)
        if not lesson:
            return None
        for key, value in update_data.items():
            if hasattr(lesson, key) and value is not None:
                setattr(lesson, key, value)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    def delete(self, lesson_id: Union[UUID, str]) -> bool:
        """Delete a lesson by ID"""
        lesson = self.get_by_id(lesson_id)
        if not lesson:
            return False
        self.db.delete(lesson)
        self.db.commit()
        return True

    def update_progress(self, student_id: UUID, lesson_id: UUID, 
                       completed: bool = True, time_spent: int = 0) -> LessonProgress:
        """Update or create lesson progress"""
        progress = self.db.query(LessonProgress).filter(
            and_(
                LessonProgress.student_id == student_id,
                LessonProgress.lesson_id == lesson_id
            )
        ).first()

        if progress:
            progress.completed = completed
            progress.time_spent += time_spent
            if completed and not progress.completed_at:
                progress.completed_at = func.now()
        else:
            progress = LessonProgress(
                student_id=student_id,
                lesson_id=lesson_id,
                completed=completed,
                time_spent=time_spent,
                completed_at=func.now() if completed else None
            )
            self.db.add(progress)

        self.db.commit()
        self.db.refresh(progress)
        return progress

    def get_student_progress(self, student_id: Union[UUID, str], course_id: Union[UUID, str]) -> List[LessonProgress]:
        """Get student's progress for all lessons in a course"""
        return self.db.query(LessonProgress).join(Lesson).filter(
            and_(
                LessonProgress.student_id == str(student_id),
                Lesson.course_id == str(course_id)
            )
        ).all()