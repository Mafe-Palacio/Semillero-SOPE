from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class SedeBase(BaseModel):
    nombre: str
    codigo: str
    activa: bool = True


class SedeCreate(SedeBase):
    pass


class SedeUpdate(BaseModel):
    nombre: Optional[str] = None
    codigo: Optional[str] = None
    activa: Optional[bool] = None


class SedeResponse(SedeBase):
    sede_id: UUID
    fecha_creacion: Optional[datetime] = None
    fecha_edicion: Optional[datetime] = None
    id_usuario_crea: Optional[UUID] = None
    id_usuario_edita: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)
