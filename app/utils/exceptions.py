from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog
from starlette.requests import Request

logger = structlog.get_logger(__name__)

# Pydantic model for standardized error responses
class ErrorResponse(BaseModel):
    detail: str | list[str]

# Custom exception for health check failures
class ServiceUnavailableError(Exception):
    def __init__(self, detail: str):
        self.detail = detail

async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled error",
        exc_info=exc,
        url=str(request.url) if isinstance(request, Request) else "Unknown",
        method=request.method if isinstance(request, Request) else "Unknown",
        request_type=str(type(request))
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "Validation error",
        errors=exc.errors(),
        url=str(request.url) if isinstance(request, Request) else "Unknown",
        method=request.method if isinstance(request, Request) else "Unknown",
        request_type=str(type(request))
    )
    return JSONResponse(
        status_code=422,
        content={"detail": [str(error) for error in exc.errors()]}
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTP error",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url) if isinstance(request, Request) else "Unknown",
        method=request.method if isinstance(request, Request) else "Unknown",
        request_type=str(type(request))
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)}
    )

async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError):
    logger.warning(
        "Service unavailable",
        detail=exc.detail,
        url=str(request.url) if isinstance(request, Request) else "Unknown",
        method=request.method if isinstance(request, Request) else "Unknown",
        request_type=str(type(request))
    )
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc.detail)}
    )

# Dictionary to register handlers with FastAPI
exception_handlers = {
    Exception: generic_exception_handler,
    RequestValidationError: validation_exception_handler,
    HTTPException: http_exception_handler,
    ServiceUnavailableError: service_unavailable_handler
}