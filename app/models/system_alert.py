from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class SystemAlert(Base):
    __tablename__ = "system_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    alert_type = Column(String(50), nullable=False)  # warning, info, error
    severity = Column(String(20), nullable=False)  # High, Medium, Low
    message = Column(String(500), nullable=False)
    affected_resource = Column(String(100))
    is_resolved = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    resolved_at = Column(DateTime)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
