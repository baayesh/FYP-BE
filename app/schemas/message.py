from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ParticipantInfo(BaseModel):
    id: str
    name: str
    avatar: Optional[str] = None
    role: str

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    participant_ids: List[str] = Field(..., min_length=1, max_length=50)
    subject: Optional[str] = Field(None, max_length=255)
    context_type: Optional[str] = None
    context_id: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    subject: Optional[str] = None
    type: str
    context_type: Optional[str] = None
    context_id: Optional[str] = None
    last_message_at: Optional[datetime] = None
    last_preview: Optional[str] = None
    unread_count: int = 0
    participants: List[ParticipantInfo] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConversationListItem(BaseModel):
    id: str
    subject: Optional[str] = None
    type: str
    last_preview: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    other_participants: List[ParticipantInfo] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageSend(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    sender_name: str = ""
    sender_avatar: Optional[str] = None
    content: str
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class UnreadCountResponse(BaseModel):
    total_unread: int


class ConversationListResponse(BaseModel):
    conversations: List[ConversationListItem]
    total: int
    page: int
    limit: int
    total_pages: int
