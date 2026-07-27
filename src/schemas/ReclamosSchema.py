from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from src.entities.Enums import EstadoReclamo


class ReclamoBase(BaseModel):
    """Campos base que comparten la creación y lectura de un Reclamo."""

    objetoEnCustodia_id: UUID
    usuario_id: UUID
    evidencia_url: Optional[str] = None
    es_presencial: bool


class ReclamoCreate(ReclamoBase):
    """Esquema utilizado para crear un nuevo Reclamo."""

    pass


class ReclamoUpdate(BaseModel):
    """Esquema para actualizar un Reclamo existente (ej. cuando se revisa)."""

    estado: Optional[EstadoReclamo] = None
    fecha_revision: Optional[datetime] = None
    motivo_rechazo: Optional[str] = None
    fecha_cita: Optional[datetime] = None
    horario_cita: Optional[str] = None


class ReclamoResponse(ReclamoBase):
    """Esquema para devolver la información de un Reclamo."""

    reclamo_id: UUID
    estado: EstadoReclamo
    fecha_envio: datetime
    fecha_revision: Optional[datetime] = None
    motivo_rechazo: Optional[str] = None
    fecha_cita: Optional[datetime] = None
    horario_cita: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
