import json
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sqlfunc
from typing import List, Optional, Dict, Any
from uuid import uuid4

from app.models.forum import ForumThread, ForumReply, ThreadCategory
from app.models.user import User
from app.models.course import Course
from app.core.exceptions import NotFoundError, ValidationError


class ForumService:
    def __init__(self, db: Session):
        self.db = db

    def get_threads(self, course_id: Optional[str] = None) -> Dict[str, Any]:
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

    def _thread_to_dict(self, thread: ForumThread, author: User, course: Course, reply_count: int) -> Dict[str, Any]:
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
