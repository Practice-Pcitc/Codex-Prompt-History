from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"


class ApiError(BaseModel):
    code: str
    message: str
    details: None = None
    request_id: str


class ErrorResponse(BaseModel):
    error: ApiError
