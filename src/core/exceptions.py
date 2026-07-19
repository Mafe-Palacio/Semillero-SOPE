"""
Excepciones de app para manejo unificado de errores en la API.
Cada excepción se traduce a una respuesta HTTP estándar.
"""

from fastapi import status


class AppException(Exception):
    """Base para excepciones de la API con código HTTP y mensaje."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str | None = None,
        details: dict | list | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.code = code or "ERROR"
        self.details = details
        super().__init__(message)


class NotFoundError(AppException):
    """Recurso no encontrado (404)."""

    def __init__(
        self, message: str = "Recurso no encontrado", details: dict | list | None = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            details=details,
        )


class ConflictError(AppException):
    """Conflicto: recurso duplicado o regla de negocio (409 o 400)."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_409_CONFLICT,
        details: dict | list | None = None,
    ):
        super().__init__(
            message=message, status_code=status_code, code="CONFLICT", details=details
        )


class BadRequestError(AppException):
    """Solicitud inválida (400)."""

    def __init__(self, message: str, details: dict | list | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="BAD_REQUEST",
            details=details,
        )


class ValidationError(AppException):
    """Error de validación de datos (422)."""

    def __init__(self, message: str, details: dict | list | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            details=details,
        )
