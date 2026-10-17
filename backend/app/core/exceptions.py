"""Custom exceptions and central exception handlers for FastAPI."""

import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("menu_translator.exceptions")


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ModelServiceUnavailableError(AppException):
    """Raised when the local VLM engine (Ollama) cannot be reached."""

    def __init__(self, message: str = "Local AI model service is unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="MODEL_SERVICE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


class ModelInferenceError(AppException):
    """Raised when the VLM extraction fails or returns malformed data."""

    def __init__(self, message: str = "Model inference failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="MODEL_INFERENCE_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


class InvalidImageError(AppException):
    """Raised when an uploaded file is not a valid or readable image."""

    def __init__(self, message: str = "Invalid image provided", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="INVALID_IMAGE",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class ServerOverloadedError(AppException):
    """Raised when concurrent request capacity is exceeded."""

    def __init__(
        self,
        message: str = "Server is currently experiencing high load. Please retry shortly.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="SERVER_OVERLOADED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide exception handlers."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.error(f"Application error [{exc.code}]: {exc.message} - Path: {request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning(f"Request validation error on {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Input validation failed",
                    "details": exc.errors(),
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = f"HTTP_{exc.status_code}"
        message = "HTTP error"
        details: Dict[str, Any] = {}

        if isinstance(exc.detail, str):
            message = exc.detail
        elif isinstance(exc.detail, dict):
            details = exc.detail
            message = str(exc.detail.get("message") or exc.detail.get("error") or "HTTP error")
            code = str(exc.detail.get("code") or code)
        elif isinstance(exc.detail, list):
            details = {"errors": exc.detail}
            message = "Validation failed for request parameters"

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "details": details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled exception on {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "UNEXPECTED_ERROR",
                    "message": "An unexpected server error occurred",
                    "details": {},
                }
            },
        )
