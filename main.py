from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import LoggingMiddleware
from app.core.database import init_db

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthMiddleware)

    # Setup exception handlers
    setup_exception_handlers(app)

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "success": True,
            "message": "Welcome to Retinify LMS API",
            "version": settings.VERSION,
            "docs": "/docs",
            "api": settings.API_V1_STR
        }

    # Basic health check endpoint (always available)
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": settings.VERSION}

    # Lazy import and include API routes
    router_error = None
    try:
        from app.api.v1.router import api_router
        app.include_router(api_router, prefix=settings.API_V1_STR)
    except ImportError as e:
        router_error = str(e)
        print(f"Warning: Could not import API router: {router_error}")

    return app

app = create_app()

init_db()
# seed_db()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )