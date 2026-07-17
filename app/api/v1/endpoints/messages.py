from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.services.message import MessageService
from app.schemas.common import APIResponse
from app.schemas.message import (
    ConversationCreate,
    MessageSend,
)

router = APIRouter()

ERR_USER_NOT_FOUND = "User not found"


def _get_user(email: str, db: Session) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail=ERR_USER_NOT_FOUND)
    return user


@router.get("/messages/eligible-recipients", response_model=APIResponse)
async def get_eligible_recipients(
    email: str = Query(..., description="User email"),
    db: Session = Depends(get_db),
):
    try:
        current_user = _get_user(email, db)
        service = MessageService(db)
        recipients = service.get_eligible_recipients(current_user)
        return APIResponse(success=True, data={"recipients": recipients})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages/conversations", response_model=APIResponse)
async def create_conversation(
    data: ConversationCreate,
    email: str = Query(..., description="User email"),
    db: Session = Depends(get_db),
):
    try:
        current_user = _get_user(email, db)
        service = MessageService(db)
        conv = service.create_conversation(
            current_user=current_user,
            participant_ids=data.participant_ids,
            subject=data.subject,
            context_type=data.context_type,
            context_id=data.context_id,
        )
        result = service.get_conversation_by_id(conv.id, current_user)
        return APIResponse(success=True, data=result, message="Conversation created")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/conversations", response_model=APIResponse)
async def list_conversations(
    email: str = Query(..., description="User email"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        current_user = _get_user(email, db)
        service = MessageService(db)
        result = service.get_user_conversations(current_user, page=page, limit=limit)
        return APIResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/conversations/{conversation_id}", response_model=APIResponse)
async def get_conversation(
    conversation_id: str,
    email: str = Query(..., description="User email"),
    db: Session = Depends(get_db),
):
    try:
        current_user = _get_user(email, db)
        service = MessageService(db)
        result = service.get_conversation_by_id(conversation_id, current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return APIResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/conversations/{conversation_id}/messages", response_model=APIResponse)
async def get_messages(
    conversation_id: str,
    email: str = Query(..., description="User email"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        current_user = _get_user(email, db)
        service = MessageService(db)
        result = service.get_conversation_messages(conversation_id, current_user, page=page, limit=limit)
        if result is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return APIResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages/conversations/{conversation_id}/messages", response_model=APIResponse)
async def send_message(
    conversation_id: str,
    data: MessageSend,
    email: str = Query(..., description="User email"),
    db: Session = Depends(get_db),
):
    try:
        current_user = _get_user(email, db)
        service = MessageService(db)
        message = service.send_message(conversation_id, current_user, data.content)
        if not message:
            raise HTTPException(status_code=404, detail="Conversation not found")

        msg_data = {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "sender_id": message.sender_id,
            "sender_name": current_user.full_name,
            "sender_avatar": current_user.avatar,
            "content": message.content,
            "is_read": message.is_read,
            "read_at": message.read_at,
            "created_at": message.created_at,
        }
        return APIResponse(success=True, data=msg_data, message="Message sent")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/messages/conversations/{conversation_id}/read", response_model=APIResponse)
async def mark_as_read(
    conversation_id: str,
    email: str = Query(..., description="User email"),
    db: Session = Depends(get_db),
):
    try:
        current_user = _get_user(email, db)
        service = MessageService(db)
        result = service.mark_as_read(conversation_id, current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return APIResponse(success=True, message="Marked as read")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/unread-count", response_model=APIResponse)
async def get_unread_count(
    email: str = Query(..., description="User email"),
    db: Session = Depends(get_db),
):
    try:
        current_user = _get_user(email, db)
        service = MessageService(db)
        count = service.get_unread_count(current_user)
        return APIResponse(success=True, data={"total_unread": count})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

