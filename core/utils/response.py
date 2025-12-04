# core/utils/response.py

from typing import Any, Dict
from fastapi.responses import JSONResponse


def json_ok(data: Any) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={"success": True, "data": data},
    )


def json_error(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "error": message},
    )
