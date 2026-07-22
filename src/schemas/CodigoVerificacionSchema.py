from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class TipoCodigoVerificacion(str, Enum):
    """Propósitos de generación de códigos OTP (Contraseña de un solo uso)."""

    REGISTRO = "REGISTRO"
    RECUPERACION_PASSWORD = "RECUPERACION_PASSWORD"


class CodigoVerificacionBase(BaseModel):
    """Información básica vinculada a un código de verificación."""

    usuario_id: UUID
    tipo: TipoCodigoVerificacion


class CodigoVerificacionCreate(CodigoVerificacionBase):
    """Datos requeridos para generar y almacenar un nuevo código OTP."""

    codigo: str
    expira_en: datetime


class VerificarCodigoRequest(BaseModel):
    """Payload que envía el cliente para validar el OTP recibido."""

    usuario_id: UUID
    codigo: str
    tipo: TipoCodigoVerificacion


class CodigoVerificacionResponse(CodigoVerificacionBase):
    """Esquema de respuesta para los datos de un código de verificación."""

    codigoVerificacion_id: UUID
    expira_en: datetime
    usado: bool

    model_config = ConfigDict(from_attributes=True)
