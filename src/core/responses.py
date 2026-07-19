"""
Estructuras de respuesta estándar para la API.
Todas las respuestas exitosas y de error siguen un formato uniforme.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiErrorDetail(BaseModel):
    """Detalle de error en respuestas de fallo."""

    code: str = Field(..., description="Código de error")
    message: str = Field(..., description="Mensaje legible")
    details: dict | list | None = Field(
        None, description="Detalles adicionales (ej. errores de validación)"
    )


class ApiErrorResponse(BaseModel):
    """Estructura de respuesta para errores."""

    success: bool = Field(False, description="Indica que la petición falló")
    error: ApiErrorDetail = Field(..., description="Información del error")


class ApiResponse(BaseModel, Generic[T]):
    """Estructura de respuesta para operaciones exitosas."""

    success: bool = Field(True, description="Indica que la petición fue exitosa")
    data: T = Field(..., description="Datos devueltos")
    message: str | None = Field(None, description="Mensaje opcional")


def success_response(data: Any, message: str | None = None) -> dict[str, Any]:
    """Construye un diccionario de respuesta exitosa (para serialización JSON)."""
    return {"success": True, "data": data, "message": message}


def error_response(
    code: str, message: str, details: dict | list | None = None
) -> dict[str, Any]:
    """Construye un diccionario de respuesta de error."""
    return {
        "success": False,
        "error": {"code": code, "message": message, "details": details},
    }
