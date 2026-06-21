#!/usr/bin/env python3
"""Seed sample data for dashboard tables"""

from app.core.database import SessionLocal, engine
from app.models.system_health import SystemHealth
from app.models.activity_log import ActivityLog
from app.models.system_alert import SystemAlert
from app.models.user import User
from datetime import datetime, timedelta
import uuid

# Create tables if they don't exist
SystemHealth.metadata.create_all(bind=engine)
ActivityLog.metadata.create_all(bind=engine)
SystemAlert.metadata.create_all(bind=engine)

db = SessionLocal()

# Add sample system health records
print("Adding system health records...")
for i in range(5):
    health = SystemHealth(
        api_uptime=92 + i,
        response_time=100 + (i * 5),
        error_rate=0.5 + (i * 0.1),
        database_status="connected",
        active_connections=15 + i,
        timestamp=datetime.now() - timedelta(days=i)
    )
    db.add(health)

# Add sample activity logs
print("Adding activity logs...")
users = db.query(User).limit(3).all()
if users:
    for user in users:
        for j, action in enumerate(["LOGIN", "CREATE", "UPDATE", "SUBMIT"]):
            log = ActivityLog(
                user_id=user.id,
                action=action,
                entity_type="course",
                entity_id=str(uuid.uuid4())[:8],
                details=f"{action} performed",
                timestamp=datetime.now() - timedelta(hours=j*2)
            )
            db.add(log)

# Add sample system alerts
print("Adding system alerts...")
alerts_data = [
    ("warning", "Database response time high", "Database"),
    ("error", "API endpoint timeout", "API"),
    ("info", "System maintenance scheduled", "System"),
]
for alert_type, message, resource in alerts_data:
    alert = SystemAlert(
        alert_type=alert_type,
        severity="High" if alert_type == "error" else ("Medium" if alert_type == "warning" else "Low"),
        message=message,
        affected_resource=resource,
        is_resolved=False
    )
    db.add(alert)

db.commit()
db.close()
print("✓ Sample data added successfully!")
