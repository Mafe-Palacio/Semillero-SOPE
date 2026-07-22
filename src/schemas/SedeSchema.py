from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class SedeBase(BaseModel):
    """
    Esquema base para representar la información común de una sede de la institución.
    """

    nombre: str
    codigo: str
    activa: bool = True


class SedeCreate(SedeBase):
    """
    Esquema utilizado para la creación de una nueva sede.
    Hereda todos los campos obligatorios de SedeBase.
    """

    pass


class SedeUpdate(BaseModel):
    """
    Esquema para la actualización parcial de una sede (PATCH/PUT).
    Todos los campos son opcionales para permitir modificaciones individuales.
    """

    nombre: Optional[str] = None
    codigo: Optional[str] = None
    activa: Optional[bool] = None


class SedeResponse(SedeBase):
    """
    Esquema de respuesta para las peticiones HTTP que retornan datos de una sede.
    """

    sede_id: UUID
    fecha_creacion: Optional[datetime] = None
    fecha_edicion: Optional[datetime] = None
    usuario_crea_id: Optional[UUID] = None
    usuario_edita_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)
