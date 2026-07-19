"""
Manejadores globales de excepciones para respuestas de error estándar.
"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from src.core.exceptions import AppException
from src.core.responses import error_response


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Convierte AppException en respuesta JSON con estructura estándar."""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details,
        ),
    )


async def http_exception_handler(request: Request, exc) -> JSONResponse:
    """Convierte HTTPException de FastAPI en respuesta estándar."""
    detail = exc.detail
    if isinstance(detail, dict):
        message = detail.get("msg", detail.get("message", str(detail)))
        details = detail.get("details", detail)
    elif isinstance(detail, list):
        message = "Error de validación o solicitud"
        details = detail
    else:
        message = str(detail)
        details = None
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code="HTTP_ERROR",
            message=message,
            details=details,
        ),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convierte errores de validación Pydantic (422) en respuesta estándar."""
    errors = exc.errors()
    details = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in errors]
    return JSONResponse(
        status_code=422,
        content=error_response(
            code="VALIDATION_ERROR",
            message="Error de validación en los datos enviados",
            details=details,
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Captura cualquier otra excepción y devuelve 500 con formato estándar."""
    return JSONResponse(
        status_code=500,
        content=error_response(
            code="INTERNAL_ERROR",
            message="Error interno del servidor. Intente más tarde.",
            details=None,
        ),
    )
