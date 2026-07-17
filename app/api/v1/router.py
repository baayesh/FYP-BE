from fastapi import APIRouter

from app.api.v1.endpoints import auth, student, teacher, parent, admin, student_performance, courses, lessons, calendar_event, messages, attendance

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(student.router, prefix="/student", tags=["student"])
api_router.include_router(student_performance.router, prefix="/student/performance", tags=["student-performance"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(lessons.router, prefix="/courses", tags=["lessons"])
api_router.include_router(teacher.router, prefix="/teacher", tags=["teacher"])
api_router.include_router(parent.router, prefix="/parent", tags=["parent"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

api_router.include_router(calendar_event.router, prefix="/student", tags=["calendar"])
api_router.include_router(messages.router, prefix="", tags=["messages"])
api_router.include_router(attendance.teacher_router, prefix="/teacher", tags=["attendance"])
api_router.include_router(attendance.parent_router, prefix="/parent", tags=["attendance"])