from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional, Dict, Any


from app.repositories.course import CourseRepository
from app.models.user import User, UserRole
from app.models.course import Course, CourseEnrollment, CourseStatus, EnrollmentStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.services.student import StudentService


class CourseService:
    def __init__(self, db: Session):
        self.db = db
        self.course_repo = CourseRepository(db)

    def get_student_courses(
        self,
        email: str,
        status_filter: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all courses for a specific student with progress tracking"""
        student = StudentService(self.db).get_student_by_email(email)

        query = self.db.query(
            CourseEnrollment,
            Course,
            User.first_name,
            User.last_name,
            User.avatar.label('instructor_avatar')
        ).join(
            Course, CourseEnrollment.course_id == Course.id
        ).join(
            User, Course.teacher_id == User.id
        ).filter(
            CourseEnrollment.student_id == student.id
        )

        if status_filter:
            query = query.filter(CourseEnrollment.status == status_filter)
        if category:
            query = query.filter(Course.category == category)

        enrollments = query.all()

        courses = []
        for enrollment, course, first_name, last_name, instructor_avatar in enrollments:
            enrolled_count = self.course_repo.count_enrolled_students(course.id)

            courses.append({
                "id": str(course.id),
                "title": course.title,
                "description": course.description,
                "category": course.category,
                "level": course.level,
                "duration": course.duration,
                "thumbnail": course.thumbnail,
                "teacher_id": str(course.teacher_id),
                "instructor": f"{first_name} {last_name}",
                "instructor_avatar": instructor_avatar,
                "status": course.status,
                "enrolled": enrolled_count,
                "progress": float(enrollment.progress or 0),
                "enrollment_date": enrollment.enrollment_date,
                "created_at": course.created_at,
                "updated_at": course.updated_at
            })

        return {"courses": courses, "count": len(courses)}

    def get_course_detail(
        self,
        course_id: str,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed course information with optional student progress"""
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise NotFoundError("Course not found")

        teacher = self.db.query(User).filter(User.id == course.teacher_id).first()

        enrolled_count = self.db.query(func.count(CourseEnrollment.id)).filter(
            CourseEnrollment.course_id == course.id,
            CourseEnrollment.status == EnrollmentStatus.ACTIVE
        ).scalar() or 0

        progress = 0
        enrollment_date = None
        if email:
            student = StudentService(self.db).get_student_by_email(email)
            enrollment = self.db.query(CourseEnrollment).filter(
                and_(
                    CourseEnrollment.student_id == student.id,
                    CourseEnrollment.course_id == course_id
                )
            ).first()
            if enrollment:
                progress = float(enrollment.progress or 0)
                enrollment_date = enrollment.enrollment_date

        return {
            "id": str(course.id),
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "level": course.level,
            "duration": course.duration,
            "thumbnail": course.thumbnail,
            "teacher_id": str(course.teacher_id),
            "instructor": teacher.full_name if teacher else None,
            "instructor_avatar": teacher.avatar if teacher else None,
            "status": course.status,
            "enrolled": enrolled_count,
            "progress": progress,
            "enrollment_date": enrollment_date,
            "created_at": course.created_at,
            "updated_at": course.updated_at
        }

    def create_course(self, teacher_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new course"""
        teacher = self.db.query(User).filter(User.id == teacher_id).first()
        if not teacher or teacher.role != UserRole.TEACHER:
            raise ValidationError("Only teachers can create courses")

        course = Course(
            teacher_id=teacher_id,
            title=data["title"],
            description=data.get("description"),
            category=data.get("category"),
            level=data.get("level"),
            duration=data.get("duration"),
            thumbnail=data.get("thumbnail"),
            status=CourseStatus.ACTIVE
        )
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)

        return {
            "id": str(course.id),
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "level": course.level,
            "duration": course.duration,
            "thumbnail": course.thumbnail,
            "teacher_id": str(course.teacher_id),
            "instructor": teacher.full_name,
            "instructor_avatar": teacher.avatar,
            "status": course.status,
            "enrolled": 0,
            "progress": 0,
            "enrollment_date": None,
            "created_at": course.created_at,
            "updated_at": course.updated_at
        }

    def update_course(self, teacher_id: str, course_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a course with ownership verification"""
        teacher = self.db.query(User).filter(User.id == teacher_id).first()
        if not teacher or teacher.role != UserRole.TEACHER:
            raise ValidationError("Only teachers can update courses")

        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise NotFoundError("Course not found")

        if str(course.teacher_id) != str(teacher_id):
            raise ValidationError("You can only update your own courses")

        for key, value in data.items():
            if hasattr(course, key) and value is not None:
                setattr(course, key, value)

        self.db.commit()
        self.db.refresh(course)

        enrolled_count = self.course_repo.count_enrolled_students(course.id)

        return {
            "id": str(course.id),
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "level": course.level,
            "duration": course.duration,
            "thumbnail": course.thumbnail,
            "teacher_id": str(course.teacher_id),
            "instructor": teacher.full_name,
            "instructor_avatar": teacher.avatar,
            "status": course.status,
            "enrolled": enrolled_count,
            "progress": 0,
            "enrollment_date": None,
            "created_at": course.created_at,
            "updated_at": course.updated_at
        }

    def delete_course(self, teacher_id: str, course_id: str) -> None:
        """Delete a course with ownership verification"""
        teacher = self.db.query(User).filter(User.id == teacher_id).first()
        if not teacher or teacher.role != UserRole.TEACHER:
            raise ValidationError("Only teachers can delete courses")

        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise NotFoundError("Course not found")

        if str(course.teacher_id) != str(teacher_id):
            raise ValidationError("You can only delete your own courses")

        self.db.delete(course)
        self.db.commit()

    def get_all_courses(
        self,
        category: Optional[str] = None,
        level: Optional[str] = None,
        status_filter: Optional[str] = "active",
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get all available courses"""
        query = self.db.query(Course).join(User, Course.teacher_id == User.id)

        if status_filter:
            query = query.filter(Course.status == status_filter)
        if category:
            query = query.filter(Course.category == category)
        if level:
            query = query.filter(Course.level == level)

        courses_data = query.limit(limit).all()

        courses = []
        for course in courses_data:
            teacher = self.db.query(User).filter(User.id == course.teacher_id).first()

            enrolled_count = self.course_repo.count_enrolled_students(course.id)

            courses.append({
                "id": str(course.id),
                "title": course.title,
                "description": course.description,
                "category": course.category,
                "level": course.level,
                "duration": course.duration,
                "thumbnail": course.thumbnail,
                "teacher_id": str(course.teacher_id),
                "instructor": teacher.full_name if teacher else None,
                "instructor_avatar": teacher.avatar if teacher else None,
                "status": course.status,
                "enrolled": enrolled_count,
                "progress": 0,
                "enrollment_date": None,
                "created_at": course.created_at,
                "updated_at": course.updated_at
            })

        return {"courses": courses, "count": len(courses)}
