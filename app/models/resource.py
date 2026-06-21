from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class ResourceType(str, enum.Enum):
    DOCUMENT = "document"
    VIDEO = "video"
    LINK = "link"

class Resource(Base):
    __tablename__ = "resources"

    id = Column(String(36), primary_key=True, default=uuid.uuid4, index=True)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    uploaded_by = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    type = Column(Enum(ResourceType), nullable=False)
    url = Column(Text, nullable=False)
    description = Column(Text)
    file_size = Column(Integer)
    downloads = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=func.now())

    # Relationships
    course = relationship("Course")
    uploader = relationship("User")