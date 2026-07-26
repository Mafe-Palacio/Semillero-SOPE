from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class RespuestaSeguridadBase(BaseModel):
    """Campos fundamentales para una respuesta de seguridad."""

    reclamo_id: UUID
    preguntaSeguridad_id: UUID
    respuesta_usuario: str


class RespuestaSeguridadCreate(RespuestaSeguridadBase):
    """Esquema para cuando el usuario envía su respuesta."""

    pass


class RespuestaSeguridadUpdate(BaseModel):
    """Esquema para actualizar una respuesta (por ejemplo, corrección antes de envío final)."""

    respuesta_usuario: Optional[str] = None


class RespuestaSeguridadResponse(RespuestaSeguridadBase):
    """Esquema de salida para visualizar la respuesta guardada."""

    respuestaSeguridad_id: UUID

    model_config = ConfigDict(from_attributes=True)
