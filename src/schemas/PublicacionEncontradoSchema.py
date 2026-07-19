from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class PublicacionEncontradoBase(BaseModel):
    usuario_id: UUID
    categoria: str
    descripcion: str
    lugar_hallado: str
    fecha_hallazgo: datetime
    lugar_entrega: str
    imagen_url: str
    estado: str
    motivo_rechazo: Optional[str] = None
    eliminacionSolicitada: Optional[str] = None


class PublicacionEncontradoCreate(PublicacionEncontradoBase):
    pass


class PublicacionEncontradoUpdate(BaseModel):
    categoria: Optional[str] = None
    descripcion: Optional[str] = None
    lugar_hallado: Optional[str] = None
    fecha_hallazgo: Optional[datetime] = None
    lugar_entrega: Optional[str] = None
    imagen_url: Optional[str] = None
    estado: Optional[str] = None
    motivo_rechazo: Optional[str] = None
    eliminacionSolicitada: Optional[str] = None
    id_usuario_edita: Optional[UUID] = None


class PublicacionEncontradoResponse(PublicacionEncontradoBase):
    PublicacionEncontrado_id: UUID
    fecha_publicacion: datetime
    fecha_creacion: Optional[datetime] = None
    fecha_edicion: Optional[datetime] = None
    id_usuario_crea: Optional[UUID] = None
    id_usuario_edita: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)
