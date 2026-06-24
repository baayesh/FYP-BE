from pydantic import BaseModel, Field
from typing import Optional


class QuizAnswerItem(BaseModel):
    question_id: str = Field(..., description="ID of the question")
    answer: str = Field(..., description="Student's answer")


class QuizSubmitRequest(BaseModel):
    student_id: str = Field(..., description="ID of the student")
    answers: list[QuizAnswerItem] = Field(..., description="List of question answers")


class QuizSubmitResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    student_id: str
    score: float
    total: float
    passed: bool
    correct_count: int
    total_questions: int
