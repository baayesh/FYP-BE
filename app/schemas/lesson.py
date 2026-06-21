from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID

class QuizItem(BaseModel):
    question: str  
    answer: str   

class AssignmentItem(BaseModel):
    title: str    
    description: str  

class LessonBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content: Optional[str] = None
    duration: Optional[str] = Field(None, description="Display duration e.g. '15 min'")
    status: Optional[str] = Field("unlocked", pattern="^(unlocked|locked)$")
    video_link: Optional[str] = Field(None, description="YouTube video URL")
    quizzes: List[QuizItem] = []
    assignments: List[AssignmentItem] = []

class LessonCreate(LessonBase):
    order_index: int = Field(..., ge=0)

class LessonUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    content: Optional[str] = None
    duration: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(unlocked|locked)$")
    video_link: Optional[str] = Field(None, description="YouTube video URL")
    quizzes: Optional[List[QuizItem]] = None
    assignments: Optional[List[AssignmentItem]] = None

class LessonResponse(LessonBase):
    id: UUID
    course_id: UUID
    order_index: int
    progress: float = 0.0

    class Config:
        from_attributes = True

class LessonListResponse(BaseModel):
    lessons: List[LessonResponse]
    count: int

class LessonCompletionRequest(BaseModel):
    lesson_id: Optional[UUID] = Field(None, description="ID of the lesson to mark as completed")

class StudentLessonAnswerRequest(BaseModel):
    lesson_id: str = Field(..., description="ID of the lesson")
    student_id: str = Field(..., description="ID of the student")
    answers: str = Field(..., description="Student answers mapped to questions (e.g., {'q1': 'answer1', 'q2': 'answer2'})")

class StudentLessonAnswerResponse(BaseModel):
    id: str
    lesson_id: str
    student_id: str
    answers: dict
    question_list_1: dict
    score: Optional[int] = None  # AI evaluation score out of 10
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
    time_spent: Optional[int] = Field(None, ge=0, description="Time spent on lesson in minutes")
    user_input: Optional[str] = Field(None, description="Input message for the AI model")
   