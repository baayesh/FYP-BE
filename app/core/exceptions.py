from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)

class APIException(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(status_code=status_code, detail=message)

class AuthenticationError(APIException):
    def __init__(self, message: str = "Authentication failed", details: dict = None):
        super().__init__(
            status_code=401,
            code="AUTHENTICATION_ERROR",
            message=message,
            details=details
        )

class AuthorizationError(APIException):
    def __init__(self, message: str = "Access denied", details: dict = None):
        super().__init__(
            status_code=403,
            code="AUTHORIZATION_ERROR",
            message=message,
            details=details
        )

class ValidationError(APIException):
    def __init__(self, message: str = "Validation failed", details: dict = None):
        super().__init__(
            status_code=422,
            code="VALIDATION_ERROR",
            message=message,
            details=details
        )

class NotFoundError(APIException):
    def __init__(self, message: str = "Resource not found", details: dict = None):
        super().__init__(
            status_code=404,
            code="NOT_FOUND",
            message=message,
            details=details
        )

class ConflictError(APIException):
    def __init__(self, message: str = "Resource conflict", details: dict = None):
        super().__init__(
            status_code=409,
            code="CONFLICT_ERROR",
            message=message,
            details=details
        )

def setup_exception_handlers(app):
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        logger.error(f"API Exception: {exc.code} - {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                    "details": {}
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Convert errors to a safe format for JSON serialization
        import json
        try:
            # Try to serialize normally
            errors_data = exc.errors()
            json.dumps(errors_data)
        except (TypeError, ValueError):
            # If serialization fails, convert everything to strings
            errors_data = str(exc.errors())
        
        logger.error(f"Validation Exception: {errors_data}")
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed. Make sure your request body is correct JSON and includes required fields.",
                    "details": {"errors": errors_data}
                }
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled Exception: {type(exc).__name__} - {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred",
                    "details": {}
                }
            }
        )