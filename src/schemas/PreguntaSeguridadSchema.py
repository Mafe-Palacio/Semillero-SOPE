from typing import List
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator

MIN_PREGUNTAS = 1
MAX_PREGUNTAS = (
    10  # tope de sanidad; la administradora decide cuántas dentro de este rango
)


class PreguntaSeguridadBase(BaseModel):
    """Información base para una pregunta de seguridad vinculada a un objeto."""

    pregunta: str
    respuesta_correcta: str
    orden: int

    @field_validator("orden")
    @classmethod
    def orden_valido(cls, v: int) -> int:
        """Valida que la posición de la pregunta esté en el rango permitido (1 a 3)."""
        if not MIN_PREGUNTAS <= v <= MAX_PREGUNTAS:
            raise ValueError(
                f"El orden de la pregunta debe estar entre {MIN_PREGUNTAS} y {MAX_PREGUNTAS}"
            )
        return v


class PreguntaSeguridadCreate(PreguntaSeguridadBase):
    """Datos requeridos para la creación individual de una pregunta de seguridad."""

    pass


class PreguntasSeguridadBulkCreate(BaseModel):
    """La administradora configura la cantidad de preguntas que considere
    apropiada para un objeto (HU04)."""

    objetoEnCustodia_id: UUID
    preguntas: List[PreguntaSeguridadCreate]

    @field_validator("preguntas")
    @classmethod
    def cantidad_valida(
        cls, v: List[PreguntaSeguridadCreate]
    ) -> List[PreguntaSeguridadCreate]:
        if not MIN_PREGUNTAS <= len(v) <= MAX_PREGUNTAS:
            raise ValueError(
                f"Se debe configurar entre {MIN_PREGUNTAS} y {MAX_PREGUNTAS} preguntas por objeto"
            )
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
