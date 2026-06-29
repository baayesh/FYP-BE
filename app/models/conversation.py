from sqlalchemy import Column, String, Text, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class ConversationType(str, enum.Enum):
    DIRECT = "direct"
    GROUP = "group"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    subject = Column(String(255), nullable=True)
    type = Column(Enum(ConversationType), default=ConversationType.DIRECT, nullable=False)
    context_type = Column(String(50), nullable=True)
    context_id = Column(String(36), nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    last_preview = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")
