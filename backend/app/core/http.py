import json
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.errors import DatabaseUnavailableError, RecordNotFoundError
from app.schemas.common import ApiError, ErrorResponse

logger = logging.getLogger("uvicorn.error")


def error_response(request: Request, status: int, code: str, message: str) -> JSONResponse:
    body = ErrorResponse(
        error=ApiError(code=code, message=message, request_id=request.state.request_id)
    )
    return JSONResponse(status_code=status, content=body.model_dump())


def register_http_handlers(app: FastAPI) -> None:
    @app.middleware("http")
    async def trace_request(request: Request, call_next):
        request.state.request_id = str(uuid4())
        origin = request.headers.get("origin")
        allowed_origins = {
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:8001",
            "http://127.0.0.1:8001",
        }
        if request.method in {"POST", "PUT", "DELETE"} and origin and origin not in allowed_origins:
            return error_response(request, 403, "ORIGIN_DENIED", "不允许来自此页面的写入请求")
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(
                json.dumps(
                    {
                        "event": "request_failed",
                        "request_id": request.state.request_id,
                        "error_type": type(exc).__name__,
                    }
                )
            )
            response = error_response(request, 500, "INTERNAL_ERROR", "服务暂时无法处理请求")
        response.headers["X-Request-ID"] = request.state.request_id
        route = request.scope.get("route")
        logger.info(
            json.dumps(
                {
                    "event": "request_completed",
                    "request_id": request.state.request_id,
                    "method": request.method,
                    "route": getattr(route, "path", "unmatched"),
                    "status": response.status_code,
                    "duration_ms": round((perf_counter() - started) * 1000, 2),
                }
            )
        )
        return response

    @app.exception_handler(DatabaseUnavailableError)
    async def database_error(request: Request, _: DatabaseUnavailableError):
        return error_response(request, 503, "DATABASE_UNAVAILABLE", "Prompt History 数据库暂不可用")

    @app.exception_handler(RecordNotFoundError)
    async def missing_record(request: Request, _: RecordNotFoundError):
        return error_response(request, 404, "PROMPT_NOT_FOUND", "Prompt 记录不存在")

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, _: RequestValidationError):
        return error_response(request, 422, "INVALID_REQUEST", "请求参数无效")

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        response = error_response(
            request, exc.status_code, f"HTTP_{exc.status_code}", "请求无法处理"
        )
        if exc.headers:
            response.headers.update(exc.headers)
        return response
