from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class TipoPuntoEntrega(str, Enum):
    """Tipos de puntos físicos oficiales de entrega y custodia."""

    OFICINA = "OFICINA"
    PORTERIA = "PORTERIA"


class PuntoEntregaBase(BaseModel):
    """Información básica de un punto físico de entrega."""

    sede_id: UUID
    nombre: str
    tipo: TipoPuntoEntrega
    activa: bool = True


class PuntoEntregaCreate(PuntoEntregaBase):
    """Datos requeridos para registrar un nuevo punto de entrega."""

    pass


class PuntoEntregaUpdate(BaseModel):
    """Campos permitidos para la actualización parcial de un punto de entrega."""

    nombre: Optional[str] = None
    tipo: Optional[TipoPuntoEntrega] = None
    activa: Optional[bool] = None


class PuntoEntregaResponse(PuntoEntregaBase):
    """Esquema de respuesta pública para los datos de un punto de entrega."""

    puntoEntrega_id: UUID
    fecha_creacion: Optional[datetime] = None
    fecha_edicion: Optional[datetime] = None
    usuario_crea_id: Optional[UUID] = None
    usuario_edita_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)
