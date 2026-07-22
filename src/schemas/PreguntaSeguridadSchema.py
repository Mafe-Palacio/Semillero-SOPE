from typing import List
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator


class PreguntaSeguridadBase(BaseModel):
    """Información base para una pregunta de seguridad vinculada a un objeto."""

    pregunta: str
    respuesta_correcta: str
    orden: int

    @field_validator("orden")
    @classmethod
    def orden_valido(cls, v: int) -> int:
        """Valida que la posición de la pregunta esté en el rango permitido (1 a 3)."""
        if not 1 <= v <= 3:
            raise ValueError("El orden de la pregunta debe estar entre 1 y 3")
        return v


class PreguntaSeguridadCreate(PreguntaSeguridadBase):
    """Datos requeridos para la creación individual de una pregunta de seguridad."""

    pass


class PreguntasSeguridadBulkCreate(BaseModel):
    """La administradora configura de 1 a 3 preguntas para un objeto (HU04)."""

    objetoEnCustodia_id: UUID
    preguntas: List[PreguntaSeguridadCreate]

    @field_validator("preguntas")
    @classmethod
    def cantidad_valida(
        cls, v: List[PreguntaSeguridadCreate]
    ) -> List[PreguntaSeguridadCreate]:
        """Garantiza que la cantidad de preguntas asignadas esté estricta entre 1 y 3."""
        if not 1 <= len(v) <= 3:
            raise ValueError("Se debe configurar entre 1 y 3 preguntas por objeto")
        return v


class PreguntaSeguridadResponse(PreguntaSeguridadBase):
    """Esquema de respuesta administrativo que incluye la respuesta correcta."""

    preguntaSeguridad_id: UUID
    objetoEnCustodia_id: UUID

    model_config = ConfigDict(from_attributes=True)


class PreguntaSeguridadPublica(BaseModel):
    """Vista sin respuesta_correcta, para mostrar al usuario que va a
    responder el cuestionario (HU20)."""

    preguntaSeguridad_id: UUID
    pregunta: str
    orden: int

    model_config = ConfigDict(from_attributes=True)
