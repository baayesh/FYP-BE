from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class SystemHealth(Base):
    __tablename__ = "system_health"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    api_uptime = Column(Float, default=95.0)  # percentage
    response_time = Column(Integer, default=100)  # milliseconds
    error_rate = Column(Float, default=0.5)  # percentage
    database_status = Column(String(50), default="connected")  # connected, disconnected, slow
    active_connections = Column(Integer, default=0)
    timestamp = Column(DateTime, default=func.now(), index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
