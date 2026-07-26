from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PosibleCoincidenciaBase(BaseModel):
    """Atributos base para la creación y lectura de una posible coincidencia."""

    objetoEnCustodia_id: UUID
    reportePerdida_id: UUID
    usuario_id: UUID
    score: int
    notificado: bool = False


class PosibleCoincidenciaCreate(PosibleCoincidenciaBase):
    """Esquema para registrar un nuevo Smart Match en el sistema."""

    pass


class PosibleCoincidenciaUpdate(BaseModel):
    """Esquema para actualizar el match, usualmente para cambiar el estado 'notificado'."""

    notificado: Optional[bool] = None
    score: Optional[int] = None


class PosibleCoincidenciaResponse(PosibleCoincidenciaBase):
    """Esquema de salida que se envía al cliente."""

    posibleCoincidencia_id: UUID
    fecha_deteccion: datetime

    model_config = ConfigDict(from_attributes=True)
