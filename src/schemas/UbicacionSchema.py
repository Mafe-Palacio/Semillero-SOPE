from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum


class TipoUbicacion(str, Enum):
    """
    Tipos de ubicación permitidos para clasificar zonas en el campus.
    """

    BLOQUE = "BLOQUE"
    PORTERIA = "PORTERIA"
    ZONA_COMUN = "ZONA_COMUN"
    OTRO = "OTRO"


class UbicacionBase(BaseModel):
    """
    Esquema base para representar la información común de una ubicación física.
    """

    sede_id: UUID
    nombre: str
    tipo: TipoUbicacion
    activa: bool = True


class UbicacionCreate(UbicacionBase):
    """
    Esquema utilizado para la creación de una nueva ubicación física.
    Hereda todos los campos obligatorios de UbicacionBase.
    """

    pass


class UbicacionUpdate(BaseModel):
    """
    Esquema para la actualización parcial de una ubicación (PATCH/PUT).
    Todos los campos son opcionales para permitir modificaciones parciales.
    """

    nombre: Optional[str] = None
    tipo: Optional[TipoUbicacion] = None
    activa: Optional[bool] = None


class UbicacionResponse(UbicacionBase):
    """
    Esquema de respuesta para las peticiones HTTP que retornan información de una ubicación.
    """

    ubicacion_id: UUID
    fecha_creacion: Optional[datetime] = None
    fecha_edicion: Optional[datetime] = None
    usuario_crea_id: Optional[UUID] = None
    usuario_edita_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)
