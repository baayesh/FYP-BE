import json
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc, and_
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from openai import OpenAI


from app.repositories.user import UserRepository
from app.repositories.course import CourseRepository, LessonRepository
from app.models.user import User, UserRole
from app.models.course import Course, Lesson, EnrollmentStatus
from app.models.assignment import Assignment, AssignmentSubmission, AssignmentFile, AssignmentEnrollment, AssignmentStatus
from app.models.grade import Grade, GradeItemType
from app.models.essay import Essay, EssaySubmission
from app.models.forum import ForumThread, ForumReply, ThreadCategory
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt
from app.models.student_lesson import StudentLesson
from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.services.performance_service import PerformanceService

class StudentService:
    def __init__(self, db: Session):
        """Initialize the student service with a database session and repositories."""
        self.db = db
        self.user_repo = UserRepository(db)
        self.course_repo = CourseRepository(db)
        self.lesson_repo = LessonRepository(db)

    def get_student_by_email(self, email: str) -> User:
        """Get student user by email and validate role"""
        user = self.db.query(User).filter(
            and_(User.email == email, User.role == UserRole.STUDENT)
        ).first()
        if not user:
            raise NotFoundError("Student not found with the provided email")
        if user.status.value != "active":
            raise ValidationError("Student account is not active")
        return user

    def get_dashboard_stats(self, student_id: UUID) -> Dict[str, Any]:
        """Get student dashboard statistics"""
        print('called to get__dashboard_stats')
        # Get enrolled courses
        enrolled_courses = self.course_repo.get_enrolled_courses(student_id)
        active_courses = len(enrolled_courses)

        # Mock data for now - in real implementation, query actual data
        stats = {
            "activeCourses": active_courses,
            "upcomingAssignments": 8,  
            "completedLessons": 24,   
            "averageGrade": 85.5,     
            "recentActivity": [
                {
                    "id": "1",
                    "type": "assignment",
                    "title": "Math Assignment 1",
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "completed"
                }
            ]
        }
        
        return stats

    def _to_letter_grade(self, numeric_grade: float) -> str:
        """Helper: convert a numeric grade to a letter grade (A+ through F)."""
        if numeric_grade >= 97: return "A+"
        elif numeric_grade >= 90: return "A"
        elif numeric_grade >= 87: return "B+"
        elif numeric_grade >= 80: return "B"
        elif numeric_grade >= 77: return "C+"
        elif numeric_grade >= 70: return "C"
        elif numeric_grade >= 67: return "D+"
        elif numeric_grade >= 60: return "D"
        else: return "F"

    def get_grades(self, student_id, db=None) -> Dict[str, Any]:
        """Get all grades for a student, grouped by subject with summaries."""
        student_id_str = str(student_id)

        results = (
            self.db.query(Grade, Course)
            .join(Course, Grade.course_id == Course.id)
            .filter(Grade.student_id == student_id_str)
            .order_by(Grade.graded_at.desc())
            .all()
        )

        assignment_ids = []
        essay_ids = []
        quiz_ids = []

        for grade, course in results:
            if grade.item_type == GradeItemType.ASSIGNMENT:
                assignment_ids.append(grade.item_id)
            elif grade.item_type == GradeItemType.ESSAY:
                essay_ids.append(grade.item_id)
            elif grade.item_type == GradeItemType.QUIZ:
                quiz_ids.append(grade.item_id)

        item_names = {}

        if assignment_ids:
            item_names.update({
                a.id: a.title
                for a in self.db.query(Assignment).filter(Assignment.id.in_(assignment_ids)).all()
            })

        if essay_ids:
            item_names.update({
                e.id: e.title
                for e in self.db.query(Essay).filter(Essay.id.in_(essay_ids)).all()
            })

        if quiz_ids:
            item_names.update({
                q.id: q.title
                for q in self.db.query(Quiz).filter(Quiz.id.in_(quiz_ids)).all()
            })

        feedback_map = {}

        if assignment_ids:
            for sub in self.db.query(AssignmentSubmission).filter(
                AssignmentSubmission.assignment_id.in_(assignment_ids),
                AssignmentSubmission.student_id == student_id_str,
                AssignmentSubmission.feedback != None
            ).all():
                feedback_map[sub.assignment_id] = sub.feedback

        if essay_ids:
            for sub in self.db.query(EssaySubmission).filter(
                EssaySubmission.essay_id.in_(essay_ids),
                EssaySubmission.student_id == student_id_str,
                EssaySubmission.feedback != None
            ).all():
                feedback_map[sub.essay_id] = sub.feedback

        grades_data = []
        subject_totals = {}

        for grade, course in results:
            item_name = item_names.get(grade.item_id)
            if not item_name:
                item_name = f"{grade.item_type.value.title()}"

            percentage = float(grade.grade) if grade.grade else 0
            score = float(grade.points_earned) if grade.points_earned else None
            max_score = float(grade.points_possible) if grade.points_possible else None
            date_str = grade.graded_at.strftime("%Y-%m-%d") if grade.graded_at else None

            grades_data.append({
                "id": grade.id,
                "subject": course.title,
                "item_type": grade.item_type.value,
                "item_name": item_name,
                "score": score,
                "max_score": max_score,
                "percentage": percentage,
                "letter_grade": grade.letter_grade,
                "date": date_str,
                "feedback": feedback_map.get(grade.item_id)
            })

            if grade.course_id not in subject_totals:
                subject_totals[grade.course_id] = {
                    "subject": course.title,
                    "percentages": [],
                    "dates": []
                }
            subject_totals[grade.course_id]["percentages"].append(percentage)
            if grade.graded_at:
                subject_totals[grade.course_id]["dates"].append(grade.graded_at)

        subject_summaries = []
        for course_id, info in subject_totals.items():
            avg = sum(info["percentages"]) / len(info["percentages"])
            letter = self._to_letter_grade(avg)

            trend = "stable"
            if len(info["dates"]) >= 2:
                sorted_grades = sorted(
                    zip(info["percentages"], info["dates"]),
                    key=lambda x: x[1]
                )
                recent_avg = sorted_grades[-1][0]
                older_avg = sum(g[0] for g in sorted_grades[:-1]) / (len(sorted_grades) - 1)
                if recent_avg > older_avg + 2:
                    trend = "up"
                elif recent_avg < older_avg - 2:
                    trend = "down"

            subject_summaries.append({
                "subject": info["subject"],
                "average": round(avg, 1),
                "grade": letter,
                "trend": trend
            })

        all_percentages = [g["percentage"] for g in grades_data if g["percentage"] is not None]
        overall_average = round(sum(all_percentages) / len(all_percentages), 1) if all_percentages else 0

        return {
            "grades": grades_data,
            "subject_summaries": subject_summaries,
            "overall_average": overall_average
        }

    #courses
    def get_courses(self, student_id: UUID, status: Optional[str] = None, 
                   search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get student's enrolled courses"""
        
        # Convert status to enrollment status
        enrollment_status = None
        if status == "active":
            enrollment_status = EnrollmentStatus.ACTIVE
        elif status == "completed":
            enrollment_status = EnrollmentStatus.COMPLETED
        
        enrolled_courses = self.course_repo.get_enrolled_courses(
            student_id, 
            enrollment_status, 
            0, 
            100
        )

        courses_data = []
        for course in enrolled_courses:
            # Get enrollment info
            enrollment = self.course_repo.get_enrollment(UUID(course.id), student_id)
            
            course_data = {
                "id": str(course.id),
                "title": course.title,
                "instructor": course.teacher.full_name if course.teacher else "",
                "instructorAvatar": course.teacher.avatar if course.teacher else None,
                "description": course.description,
                "progress": float(enrollment.progress) if enrollment and enrollment.progress else 0,
                "totalLessons": len(course.lessons) if hasattr(course, 'lessons') else 0,
                "completedLessons": 0,  # TODO: Calculate from lesson progress
                "enrollmentDate": enrollment.enrollment_date.isoformat() if enrollment else None,
                "thumbnail": course.thumbnail,
                "category": course.category,
                "status": enrollment.status.value if enrollment else "active"
            }
            courses_data.append(course_data)

        # Apply search filter if provided
        if search:
            courses_data = [
                course for course in courses_data 
                if search.lower() in course["title"].lower() 
                or search.lower() in course["instructor"].lower()
            ]

        return courses_data

    def get_course_details(self, student_id: UUID, course_id: str) -> Dict[str, Any]:
        """Get detailed course information"""
        
        try:
            course_uuid = UUID(course_id)
        except ValueError:
            raise ValidationError("Invalid course ID format")

        course = self.course_repo.get_by_id(course_uuid)
        if not course:
            raise NotFoundError("Course not found")

        # Check if student is enrolled
        enrollment = self.course_repo.get_enrollment(course_uuid, student_id)
        if not enrollment:
            raise NotFoundError("Student not enrolled in this course")

        # Get lessons for the course
        lessons = self.lesson_repo.get_by_course(course_uuid)
        
        # Get student's progress
        progress_records = self.lesson_repo.get_student_progress(student_id, course_uuid)
        progress_map = {p.lesson_id: p for p in progress_records}

        # Build syllabus structure
        syllabus = []
        # Group lessons by module (simplified - assumes single module for now)
        module_data = {
            "id": "1",
            "title": "Course Content",
            "order": 1,
            "lessons": []
        }

        for lesson in lessons:
            progress = progress_map.get(lesson.id)
            lesson_data = {
                "id": str(lesson.id),
                "title": lesson.title,
                "duration": lesson.duration,
                "type": lesson.type.value,
                "completed": progress.completed if progress else False
            }
            module_data["lessons"].append(lesson_data)

        syllabus.append(module_data)

        course_detail = {
            "id": str(course.id),
            "title": course.title,
            "description": course.description,
            "instructor": {
                "id": str(course.teacher.id),
                "name": course.teacher.full_name,
                "avatar": course.teacher.avatar,
                "bio": course.teacher.bio
            },
            "syllabus": syllabus,
            "progress": float(enrollment.progress) if enrollment.progress else 0,
            "enrollmentDate": enrollment.enrollment_date.isoformat()
        }

        return course_detail

    def enroll_in_course(self, student_id: UUID, course_id: str) -> Dict[str, Any]:
        """Enroll student in a course"""
        
        try:
            course_uuid = UUID(course_id)
        except ValueError:
            raise ValidationError("Invalid course ID format")

        course = self.course_repo.get_by_id(course_uuid)
        if not course:
            raise NotFoundError("Course not found")

        # Check if already enrolled
        existing_enrollment = self.course_repo.get_enrollment(course_uuid, student_id)
        if existing_enrollment:
            raise ValidationError("Already enrolled in this course")

        # Create enrollment
        enrollment = self.course_repo.enroll_student(course_uuid, student_id)

        return {
            "enrollmentId": str(enrollment.id),
            "message": "Successfully enrolled"
        }

    def get_assignments(self, student_id: UUID, status: Optional[str] = None, 
                       course_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get student's assignments via assignment_enrollment table"""

        student_id_str = str(student_id)

        query = (
            self.db.query(
                AssignmentEnrollment,
                Assignment,
                Course
            )
            .join(Assignment, AssignmentEnrollment.assignment_id == Assignment.id)
            .join(Course, AssignmentEnrollment.course_id == Course.id)
            .filter(AssignmentEnrollment.student_id == student_id_str)
        )

        if status:
            query = query.filter(AssignmentEnrollment.status == status)
        if course_id:
            query = query.filter(AssignmentEnrollment.course_id == course_id)

        results = query.all()

        assignments = []
        for ae, assignment, course in results:
            submission = self.db.query(AssignmentSubmission).filter(
                AssignmentSubmission.assignment_id == assignment.id,
                AssignmentSubmission.student_id == student_id_str
            ).first()

            assignments.append({
                "id": str(assignment.id),
                "title": assignment.title,
                "courseId": ae.course_id,
                "courseName": course.title if course else ae.course_id,
                "description": assignment.description or "",
                "dueDate": assignment.due_date.isoformat() if assignment.due_date else None,
                "points": assignment.points,
                "status": ae.status or "pending",
                "grade": float(submission.grade) if submission and submission.grade else None,
                "submittedAt": submission.submitted_at.isoformat() if submission and submission.submitted_at else None,
                "feedback": submission.feedback if submission else None,
                "attachments": []
            })

        return assignments

    def submit_assignment(self, student_id: str, assignment_id: str,
                          content: Optional[str] = None,
                          files: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Submit an assignment — creates submission & file records, updates enrollment"""
        assignment = self.db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise NotFoundError("Assignment not found")

        enrollment = self.db.query(AssignmentEnrollment).filter(
            AssignmentEnrollment.student_id == student_id,
            AssignmentEnrollment.assignment_id == assignment_id
        ).first()
        if not enrollment:
            raise NotFoundError("Student is not enrolled in this assignment")

        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            student_id=student_id,
            content=content,
            submitted_at=datetime.utcnow(),
            status=AssignmentStatus.SUBMITTED
        )
        self.db.add(submission)
        self.db.flush()

        file_records = []
        if files:
            for f in files:
                file_record = AssignmentFile(
                    submission_id=submission.id,
                    assignment_id=assignment_id,
                    file_name=f.get("name", ""),
                    file_url=f.get("url", ""),
                    file_size=f.get("size")
                )
                self.db.add(file_record)
                file_records.append(file_record)
            self.db.flush()

        enrollment.marks = 0
        enrollment.status = "submitted"

        try:
            self.db.commit()
            self.db.refresh(submission)
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to submit assignment: {str(e)}")

        try:
            PerformanceService(self.db).log_activity(student_id, assignments_completed=1)
        except Exception:
            pass

        return {
            "submission_id": submission.id,
            "assignment_id": submission.assignment_id,
            "student_id": submission.student_id,
            "content": submission.content,
            "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
            "status": submission.status.value,
            "files": [
                {"id": f.id, "name": f.file_name, "url": f.file_url, "size": f.file_size}
                for f in file_records
            ]
        }

    def get_assignment_details(self, student_id: UUID, assignment_id: str) -> Dict[str, Any]:
        """Get detailed assignment information"""
        
        # Mock assignment detail for now
        assignment = {
            "id": assignment_id,
            "title": "Math Assignment 1",
            "description": "Complete the algebra problems",
            "instructions": "Solve all problems showing your work",
            "dueDate": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "points": 100,
            "courseId": "course-1",
            "courseName": "Mathematics",
            "status": "pending",
            "attachments": [],
            "submission": None
        }
        
        return assignment

# lesson answers submission with AI evaluation
    def submit_lesson_answers(self, lesson_id: str, student_id: str, answers: str, repetition_quiz: str = 'q1') -> Dict[str, Any]:
        """Submit student answers for a lesson and evaluate using AI"""
        # Validate that lesson exists
        lesson = self.db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise NotFoundError("Lesson not found")
        
        # Validate that student exists
        student = self.db.query(User).filter(User.id == student_id).first()
        if not student:
            raise NotFoundError("Student not found")
        
        # Evaluate answers using Gemini AI
        score = self._evaluate_answers_with_ai(lesson, answers)
        
        # Query for existing StudentLesson record
        student_lesson = self.db.query(StudentLesson).filter(
            StudentLesson.lesson_id == lesson_id,
            StudentLesson.student_id == student_id
        ).first()
        
        # If not found, create a new record
        if not student_lesson:
            student_lesson = StudentLesson(
                lesson_id=lesson_id,
                student_id=student_id,
                answers=answers,
                question_list_1={"content": answers}
            )
            self.db.add(student_lesson)
        
        # Update the appropriate result field based on repetition_quiz value
        if repetition_quiz == 'q1':
            setattr(student_lesson, "Q1_Result", score)  # type: ignore[arg-type]
        elif repetition_quiz == 'q2':
            setattr(student_lesson, "Q2_Result", score)  # type: ignore[arg-type]
        elif repetition_quiz == 'q3':
            setattr(student_lesson, "Q3_Result", score)  # type: ignore[arg-type]
        elif repetition_quiz == 'q4':
            setattr(student_lesson, "Q4_Result", score)  # type: ignore[arg-type]
        else:
            setattr(student_lesson, "Q1_Result", score)  # type: ignore[arg-type]
        
        try:
            self.db.commit()
            self.db.refresh(student_lesson)
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to save lesson answers: {str(e)}")

        try:
            PerformanceService(self.db).update_trend(student_id)
            PerformanceService(self.db).log_activity(student_id, quizzes_completed=1)
        except Exception:
            pass

        return {
            "id": str(student_lesson.id),
            "lesson_id": str(student_lesson.lesson_id),
            "student_id": str(student_lesson.student_id),
            "answers": student_lesson.answers,
            "question_list_1": student_lesson.answers,
            "score": score,
            "created_at": student_lesson.created_at.isoformat(),
            "updated_at": student_lesson.updated_at.isoformat()
        }

    def _evaluate_answers_with_ai(self, lesson: Lesson, answers: str) -> int:
        """Evaluate student answers using Groq AI"""
        
        score = 0
        try:
            client = OpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1"
            )
            
            if lesson is not None and lesson.content is not None:
                prompt = f"""Based on the following lesson content, evaluate the student's answers and give a score out of 10.

Lesson Content: {lesson.content}

Student Answers: {answers}

Please provide only a numerical score between 0 and 10, where 10 is perfect and 0 is completely incorrect. Consider the accuracy, completeness, and relevance of the answers."""
            else:
                prompt = 'Please provide a score of 0 since no lesson content is available.'
            
            print(f"Sending evaluation prompt to Groq: {prompt}")
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            
            # Extract score from response
            try:
                score_text = response.choices[0].message.content.strip()
                # Strip markdown code block wrapping if present
                if score_text.startswith("```"):
                    score_text = score_text.strip("`")
                    if score_text.startswith("json"):
                        score_text = score_text[4:]
                score_text = score_text.strip()
                score = int(float(score_text))
                score = max(0, min(10, score))  # Ensure score is between 0 and 10
            except (ValueError, AttributeError, IndexError):
                score = 0
            
            print(f"AI Evaluation Score: {score}/10")
            
        except Exception as e:
            print(f"Error evaluating answers with AI: {e}")
            score = 0
        
        return score

    def generate_lesson_quiz(self, lesson_id: str, student_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate quiz questions for a lesson using Groq AI."""
        print(f"Generating quiz for lesson_id: {lesson_id}, student_id: {student_id}")
        # Fetch lesson content from database
        lesson = self.db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise NotFoundError("Lesson not found")

        from decimal import Decimal
        hours = Decimal(str(round((lesson.duration or 0) / 60, 2)))
        
        client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )

        def _call_groq(prompt_text: str) -> str:
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt_text}],
                temperature=0.7,
            )
            text = resp.choices[0].message.content.strip()
            # Strip markdown code block wrapping if present
            if text.startswith("```"):
                text = text.strip("`")
                if text.startswith("json"):
                    text = text[4:]
            return text.strip()

        if lesson.content:
            prompt = f'''Generate 10 basic MCQ questions about "{lesson.content}".
Return ONLY a valid JSON object (no markdown, no extra text) with this exact structure:
{{
  "difficulty": "basic",
  "questions": [
    {{
      "id": 1,
      "question": "Question text here?",
      "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
      "correctAnswer": "A",
      "explanation": "Brief explanation"
    }}
  ]
}}'''

            prompt_2 = f'''Generate 10 intermediate MCQ questions about "{lesson.content}".
Return ONLY a valid JSON object (no markdown, no extra text) with this exact structure:
{{
  "difficulty": "intermediate",
  "questions": [
    {{
      "id": 1,
      "question": "Question text here?",
      "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
      "correctAnswer": "A",
      "explanation": "Brief explanation"
    }}
  ]
}}'''

            prompt_3 = f'''Generate 10 medium-advanced MCQ questions about "{lesson.content}".
Return ONLY a valid JSON object (no markdown, no extra text) with this exact structure:
{{
  "difficulty": "medium-advanced",
  "questions": [
    {{
      "id": 1,
      "question": "Question text here?",
      "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
      "correctAnswer": "A",
      "explanation": "Brief explanation"
    }}
  ]
}}'''

            prompt_4 = f'''Generate 10 advanced MCQ questions about "{lesson.content}".
Return ONLY a valid JSON object (no markdown, no extra text) with this exact structure:
{{
  "difficulty": "advanced",
  "questions": [
    {{
      "id": 1,
      "question": "Question text here?",
      "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
      "correctAnswer": "A",
      "explanation": "Brief explanation"
    }}
  ]
}}'''
        else:
            prompt = 'Please provide lesson content to generate questions.'
            prompt_2 = prompt_3 = prompt_4 = prompt

        print(f"Sending prompts to Groq")

        response_text = _call_groq(prompt)
        response_text_2 = _call_groq(prompt_2)
        response_text_3 = _call_groq(prompt_3)
        response_text_4 = _call_groq(prompt_4)

        print(f"Received quiz responses: {response_text[:100]}..., {response_text_2[:100]}..., {response_text_3[:100]}..., {response_text_4[:100]}...")
        # Save quiz data to database if student_id is provided
        if student_id:
            # Create new StudentLesson record
            student_lesson = StudentLesson(
                lesson_id=lesson_id,
                student_id=student_id,
                answers=None,
                question_list_1={"content": response_text},
                question_list_2={"content": response_text_2},
                question_list_3={"content": response_text_3},
                question_list_4={"content": response_text_4},
                Q1_Result=None
            )

            try:
                self.db.add(student_lesson)
                self.db.commit()
                self.db.refresh(student_lesson)
            except Exception as e:
                self.db.rollback()
                raise ValidationError(f"Failed to save quiz data: {str(e)}")

        try:
            PerformanceService(self.db).log_activity(
                student_id,
                lessons_viewed=1,
                hours_studied=hours
            )
        except Exception:
            pass

        return {
            "quiz_questions": response_text,
            "duration_hours": float(hours)
        }
    
    
    def submit_quiz(self, quiz_id: str, student_id: str, answers: List[Dict[str, str]]) -> Dict[str, Any]:
        """Submit answers for a quiz and get scored result."""
        quiz = self.db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise NotFoundError("Quiz not found")

        questions = self.db.query(QuizQuestion).filter(
            QuizQuestion.quiz_id == quiz_id
        ).order_by(QuizQuestion.order_index).all()

        if not questions:
            raise ValidationError("Quiz has no questions")

        answer_map = {a["question_id"]: a["answer"] for a in answers}

        correct_count = 0
        total_points = 0
        earned_points = 0

        for q in questions:
            student_ans = answer_map.get(q.id, "").strip().lower()
            correct_ans = q.correct_answer.strip().lower()
            total_points += q.points
            if student_ans == correct_ans:
                correct_count += 1
                earned_points += q.points

        score = round((earned_points / total_points) * 100, 2) if total_points > 0 else 0
        passed = score >= quiz.passing_score

        attempt = QuizAttempt(
            quiz_id=quiz_id,
            student_id=student_id,
            submitted_at=datetime.utcnow(),
            score=score,
            passed=passed,
            answers=answers
        )
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)

        try:
            PerformanceService(self.db).update_trend(student_id)
            PerformanceService(self.db).log_activity(student_id, quizzes_completed=1)
        except Exception:
            pass

        return {
            "attempt_id": attempt.id,
            "quiz_id": quiz_id,
            "student_id": student_id,
            "score": score,
            "total": float(total_points),
            "passed": passed,
            "correct_count": correct_count,
            "total_questions": len(questions),
        }

    #get spaced repetition quizzes for a student based on time intervals
    def get_spaced_repetition_quizzes(self, student_id: str) -> Dict[str, Any]:
        """Get spaced repetition quizzes for a student based on time intervals"""
        
        from datetime import datetime
        
        # Get all student lesson records for this student
        student_lessons = self.db.query(StudentLesson).filter(
            StudentLesson.student_id == student_id
        ).all()
        
        today = datetime.utcnow()
        
        for lesson in student_lessons:
            if lesson.created_at:
                days_since_creation = (today - lesson.created_at).days
                
                # Check conditions in order of priority (most recent first)
                
                # 3-7 days ago and Q2_Result is null
                if 3 <= days_since_creation < 7 and lesson.Q2_Result is None and lesson.question_list_2:
                    return {
                        "available": True,
                        "quiz_type": "spaced_repetition_2",
                        "question_type": "q2",
                        "lesson_id": str(lesson.lesson_id),
                        "quizzes": lesson.question_list_2,
                        "days_since_creation": days_since_creation
                    }
                
                # 7-14 days ago and Q3_Result is null
                elif 7 <= days_since_creation < 14 and lesson.Q3_Result is None and lesson.question_list_3:
                    return {
                        "available": True,
                        "quiz_type": "spaced_repetition_3",
                        "question_type": "q3",
                        "lesson_id": str(lesson.lesson_id),
                        "quizzes": lesson.question_list_3,
                        "days_since_creation": days_since_creation
                    }
                
                # 14-30 days ago and Q4_Result is null
                elif 14 <= days_since_creation < 30 and lesson.Q4_Result is None and lesson.question_list_4:
                    return {
                        "available": True,
                        "quiz_type": "spaced_repetition_4",
                        "question_type": "q4",
                        "lesson_id": str(lesson.lesson_id),
                        "quizzes": lesson.question_list_4,
                        "days_since_creation": days_since_creation
                    }
        
        # No quizzes available for review
        return {
            "available": False,
            "message": "No quizzes available for review at this time."
        }

    # ── Forum Methods ──
    def get_threads(self, course_id: Optional[str] = None) -> Dict[str, Any]:
        """Get all forum threads, optionally filtered by course."""
        query = (
            self.db.query(
                ForumThread,
                User,
                Course,
                sqlfunc.count(ForumReply.id).label("reply_count")
            )
            .join(User, ForumThread.author_id == User.id)
            .join(Course, ForumThread.course_id == Course.id)
            .outerjoin(ForumReply, ForumReply.thread_id == ForumThread.id)
            .group_by(ForumThread.id, User.id, Course.id)
            .order_by(ForumThread.is_pinned.desc(), ForumThread.created_at.desc())
        )

        if course_id:
            query = query.filter(ForumThread.course_id == course_id)

        results = query.all()

        threads = []
        for thread, author, course, reply_count in results:
            threads.append(self._thread_to_dict(thread, author, course, reply_count))

        total_replies = sum(t["replies"] for t in threads)
        total_likes = sum(t["likes"] for t in threads)
        total_pinned = sum(1 for t in threads if t["is_pinned"])

        return {
            "threads": threads,
            "total": len(threads),
            "total_replies": total_replies,
            "total_pinned": total_pinned,
            "total_likes": total_likes,
        }

    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        """Get a single forum thread by ID and increment its view count."""
        result = (
            self.db.query(
                ForumThread,
                User,
                Course,
                sqlfunc.count(ForumReply.id).label("reply_count")
            )
            .join(User, ForumThread.author_id == User.id)
            .join(Course, ForumThread.course_id == Course.id)
            .outerjoin(ForumReply, ForumReply.thread_id == ForumThread.id)
            .filter(ForumThread.id == thread_id)
            .group_by(ForumThread.id, User.id, Course.id)
            .first()
        )

        if not result:
            raise NotFoundError("Thread not found")

        thread, author, course, reply_count = result

        # Increment views
        thread.views += 1
        self.db.commit()

        return self._thread_to_dict(thread, author, course, reply_count)

    def create_thread(self, author_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new forum thread."""
        thread = ForumThread(
            id=str(uuid4()),
            course_id=data["course_id"],
            author_id=author_id,
            title=data["title"],
            content=data["content"],
            category=data.get("category", ThreadCategory.GENERAL.value),
            tags=json.dumps(data.get("tags", [])),
        )
        self.db.add(thread)
        self.db.commit()
        self.db.refresh(thread)

        author = self.db.query(User).filter(User.id == author_id).first()
        course = self.db.query(Course).filter(Course.id == data["course_id"]).first()

        return self._thread_to_dict(thread, author, course, 0)

    def get_replies(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all replies for a forum thread, ordered chronologically."""
        thread = self.db.query(ForumThread).filter(ForumThread.id == thread_id).first()
        if not thread:
            raise NotFoundError("Thread not found")

        results = (
            self.db.query(ForumReply, User)
            .join(User, ForumReply.author_id == User.id)
            .filter(ForumReply.thread_id == thread_id)
            .order_by(ForumReply.created_at.asc())
            .all()
        )

        return [
            {
                "id": reply.id,
                "thread_id": reply.thread_id,
                "content": reply.content,
                "author": author.full_name,
                "author_id": author.id,
                "is_answer": reply.is_answer,
                "parent_reply_id": reply.parent_reply_id,
                "created_at": reply.created_at.isoformat() if reply.created_at else None,
            }
            for reply, author in results
        ]

    def create_reply(self, thread_id: str, author_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new reply in a forum thread."""
        thread = self.db.query(ForumThread).filter(ForumThread.id == thread_id).first()
        if not thread:
            raise NotFoundError("Thread not found")

        reply = ForumReply(
            id=str(uuid4()),
            thread_id=thread_id,
            author_id=author_id,
            content=data["content"],
            parent_reply_id=data.get("parent_reply_id"),
        )
        self.db.add(reply)
        self.db.commit()
        self.db.refresh(reply)

        author = self.db.query(User).filter(User.id == author_id).first()

        return {
            "id": reply.id,
            "thread_id": reply.thread_id,
            "content": reply.content,
            "author": author.full_name if author else "",
            "author_id": author.id if author else "",
            "is_answer": reply.is_answer,
            "parent_reply_id": reply.parent_reply_id,
            "created_at": reply.created_at.isoformat() if reply.created_at else None,
        }

    def like_thread(self, thread_id: str, user_id: str, liked: bool) -> Dict[str, Any]:
        """Increment or decrement the like count on a forum thread."""
        thread = self.db.query(ForumThread).filter(ForumThread.id == thread_id).first()
        if not thread:
            raise NotFoundError("Thread not found")

        if liked:
            thread.likes = (thread.likes or 0) + 1
        else:
            thread.likes = max(0, (thread.likes or 0) - 1)

        self.db.commit()
        return {"likes": thread.likes}

    def _thread_to_dict(self, thread: ForumThread, author: User, course: Course, reply_count: int) -> Dict[str, Any]:
        """Helper: serialize a forum thread and its metadata into a dictionary."""
        tags = []
        if thread.tags:
            try:
                tags = json.loads(thread.tags) if isinstance(thread.tags, str) else thread.tags
            except (json.JSONDecodeError, TypeError):
                tags = []

        return {
            "id": thread.id,
            "title": thread.title,
            "author": author.full_name,
            "author_id": author.id,
            "course": course.title,
            "course_id": course.id,
            "content": thread.content,
            "replies": reply_count,
            "likes": thread.likes or 0,
            "is_pinned": thread.is_pinned,
            "is_resolved": thread.is_resolved,
            "views": thread.views or 0,
            "createdAt": thread.created_at.isoformat() if thread.created_at else None,
            "tags": tags,
        }

