from typing import Any, Optional

from pydantic import BaseModel


class ApiResponse(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


def ok(data: Any = None, message: str = "success") -> ApiResponse:
    return ApiResponse(code=0, message=message, data=data)


def fail(code: int, message: str, data: Any = None) -> ApiResponse:
    return ApiResponse(code=code, message=message, data=data)
