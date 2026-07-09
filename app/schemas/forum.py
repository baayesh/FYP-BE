from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CreateThreadRequest(BaseModel):
    author_id: str = Field(..., min_length=1)
    course_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    category: Optional[str] = "general"
    tags: Optional[List[str]] = []


class ThreadResponse(BaseModel):
    id: str
    title: str
    author: str
    author_id: str
    course: str
    course_id: str
    content: str
    replies: int
    likes: int
    is_pinned: bool
    is_resolved: bool
    views: int
    createdAt: str
    tags: List[str]

    class Config:
        from_attributes = True


class ThreadListResponse(BaseModel):
    threads: List[ThreadResponse]
    total: int
    total_replies: int
    total_pinned: int
    total_likes: int


class CreateReplyRequest(BaseModel):
    author_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    parent_reply_id: Optional[str] = None


class ReplyResponse(BaseModel):
    id: str
    thread_id: str
    content: str
    author: str
    author_id: str
    is_answer: bool
    parent_reply_id: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class ToggleLikeRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    liked: bool
