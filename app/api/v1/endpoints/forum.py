from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.common import APIResponse
from app.schemas.forum import (
    CreateThreadRequest,
    CreateReplyRequest,
)
from app.services.forum import ForumService

router = APIRouter()


@router.get("/forum/threads", response_model=APIResponse)
async def get_threads(
    course_id: Optional[str] = Query(None, description="Filter by course ID"),
    db: Session = Depends(get_db),
):
    """Get all forum threads"""
    try:
        service = ForumService(db)
        result = service.get_threads(course_id)
        return APIResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forum/threads/{thread_id}", response_model=APIResponse)
async def get_thread(
    thread_id: str,
    db: Session = Depends(get_db),
):
    """Get a single forum thread by ID"""
    try:
        service = ForumService(db)
        thread = service.get_thread(thread_id)
        return APIResponse(success=True, data=thread)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forum/threads", response_model=APIResponse)
async def create_thread(
    data: CreateThreadRequest,
    db: Session = Depends(get_db),
):
    """Create a new forum thread"""
    try:
        service = ForumService(db)
        thread = service.create_thread(data.author_id, data.model_dump())
        return APIResponse(success=True, data=thread, message="Thread created successfully")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forum/threads/{thread_id}/replies", response_model=APIResponse)
async def get_replies(
    thread_id: str,
    db: Session = Depends(get_db),
):
    """Get all replies for a thread"""
    try:
        service = ForumService(db)
        replies = service.get_replies(thread_id)
        return APIResponse(success=True, data={"replies": replies})
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forum/threads/{thread_id}/replies", response_model=APIResponse)
async def create_reply(
    thread_id: str,
    data: CreateReplyRequest,
    db: Session = Depends(get_db),
):
    """Add a reply to a thread"""
    try:
        service = ForumService(db)
        reply = service.create_reply(thread_id, data.author_id, data.model_dump())
        return APIResponse(success=True, data=reply, message="Reply added successfully")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
