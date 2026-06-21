from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import enum

class AssignmentStatus(str, enum.Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    GRADED = "graded"

# Assignment Base Schema
class AssignmentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    due_date: datetime
    points: int = Field(..., ge=0)

# Assignment Creation Schema
class AssignmentCreate(AssignmentBase):
    course_id: UUID
    attachments: Optional[List[str]] = []

# Assignment Response Schema
class AssignmentResponse(AssignmentBase):
    id: UUID
    course_id: UUID
    course_name: Optional[str] = None
    status: Optional[AssignmentStatus] = AssignmentStatus.PENDING
    grade: Optional[float] = None
    submitted_at: Optional[datetime] = None
    feedback: Optional[str] = None
    attachments: Optional[List[dict]] = []
    created_at: datetime

    class Config:
        from_attributes = True

# Assignment Detail Response (includes submission info)
class AssignmentDetailResponse(AssignmentResponse):
    submission: Optional[dict] = None

# Assignment Submission Schema
class AssignmentSubmissionCreate(BaseModel):
    content: Optional[str] = None
    # files handled separately in multipart form


class AssignmentSubmitFile(BaseModel):
    name: str
    url: str
    size: Optional[int] = None


class AssignmentSubmitRequest(BaseModel):
    content: Optional[str] = None
    files: List[AssignmentSubmitFile] = []


# Assignment Submission Response
class AssignmentSubmissionResponse(BaseModel):
    submission_id: UUID
    submitted_at: datetime
    message: str = "Assignment submitted successfully"

# Assignment Grading Schema
class AssignmentGrade(BaseModel):
    submission_id: UUID
    grade: float = Field(..., ge=0, le=100)
    feedback: Optional[str] = None
    rubric: Optional[List[dict]] = []

# Assignment File Schema
class AssignmentFileResponse(BaseModel):
    id: UUID
    name: str
    url: str
    type: Optional[str] = None
    size: Optional[int] = None

    class Config:
        from_attributes = True

# Teacher Assignment Submissions View
class SubmissionResponse(BaseModel):
    id: UUID
    student_id: UUID
    student_name: str
    submitted_at: datetime
    status: AssignmentStatus
    grade: Optional[float] = None
    content: Optional[str] = None
    files: List[str] = []

    class Config:
        from_attributes = True