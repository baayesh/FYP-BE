from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class ThreadCategory(str, enum.Enum):
    GENERAL = "general"
    QUESTION = "question" 
    DISCUSSION = "discussion"

class ForumThread(Base):
    __tablename__ = "forum_threads"

    id = Column(String(36), primary_key=True, default=uuid.uuid4, index=True)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(20), default=ThreadCategory.GENERAL.value)
    is_pinned = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    tags = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    course = relationship("Course")
    author = relationship("User")
    replies = relationship("ForumReply", back_populates="thread")

class ForumReply(Base):
    __tablename__ = "forum_replies"

    id = Column(String(36), primary_key=True, default=uuid.uuid4, index=True)
    thread_id = Column(String(36), ForeignKey("forum_threads.id", ondelete="CASCADE"), nullable=False)
    parent_reply_id = Column(String(36), ForeignKey("forum_replies.id", ondelete="CASCADE"))
    author_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    is_answer = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    thread = relationship("ForumThread", back_populates="replies")
    parent_reply = relationship("ForumReply", remote_side=[id])
    author = relationship("User")