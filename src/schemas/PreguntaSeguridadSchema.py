from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator

MIN_PREGUNTAS = 1
MAX_PREGUNTAS = 10  # la administradora decide cuántas dentro de este rango


class PreguntaSeguridadBase(BaseModel):
    """Información base para una pregunta de seguridad vinculada a un objeto."""

    pregunta: str
    respuesta_correcta: str


class PreguntaSeguridadCreate(PreguntaSeguridadBase):
    """Datos requeridos para la creación individual de una pregunta de
    seguridad. `orden` no se recibe aquí: el CRUD lo asigna automáticamente
    según la posición dentro de la lista enviada en el bulk-create."""

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


class PreguntaSeguridadEdit(BaseModel):
    """Payload para corregir el texto/respuesta de una pregunta puntual."""

    pregunta: Optional[str] = None
    respuesta_correcta: Optional[str] = None


class PreguntaSeguridadResponse(PreguntaSeguridadBase):
    """Esquema de respuesta administrativo que incluye la respuesta correcta."""

    preguntaSeguridad_id: UUID
    objetoEnCustodia_id: UUID
    orden: int

    model_config = ConfigDict(from_attributes=True)


class PreguntaSeguridadPublica(BaseModel):
    """Vista sin respuesta_correcta, para mostrar al usuario que va a
    responder el cuestionario (HU20)."""

    preguntaSeguridad_id: UUID
    pregunta: str
    orden: int

    model_config = ConfigDict(from_attributes=True)
