from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CategoriaObjeto(str, Enum):
    """Categorías generales para clasificación de objetos."""

    ELECTRONICOS = "ELECTRONICOS"
    DOCUMENTOS = "DOCUMENTOS"
    ROPA_Y_ACCESORIOS = "ROPA_Y_ACCESORIOS"
    BOLSOS_Y_MALETAS = "BOLSOS_Y_MALETAS"
    LLAVES = "LLAVES"
    LIBROS_Y_UTILES = "LIBROS_Y_UTILES"
    OTROS = "OTROS"


class EstadoPublicacion(str, Enum):
    """Estados del ciclo de vida y moderación de una publicación."""

    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    ELIMINACION_PENDIENTE = "ELIMINACION_PENDIENTE"
    CERRADA = "CERRADA"


class PublicacionEncontradoBase(BaseModel):
    """Información base para registrar el reporte de un objeto encontrado."""

    categoria: CategoriaObjeto
    descripcion: str
    lugar_hallazgo_id: UUID
    lugar_entrega_fisica_id: UUID
    fecha_hallazgo: date
    imagen_url: Optional[str] = None


class PublicacionEncontradoCreate(PublicacionEncontradoBase):
    """Datos requeridos para publicar un reporte de objeto hallado."""

    pass


class PublicacionEncontradoUpdate(BaseModel):
    """Campos permitidos para la edición administrativa (HU07)."""

    categoria: Optional[CategoriaObjeto] = None
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None


class PublicacionEncontradoModeracion(BaseModel):
    """Usado por la administradora para aprobar/rechazar (HU02)."""

    estado: EstadoPublicacion
    motivo_rechazo: Optional[str] = None


class PublicacionEncontradoResolverEliminacion(BaseModel):
    """Resuelve la solicitud de eliminación hecha por el usuario dueño de la publicación."""

    aprobar: bool
    motivo: Optional[str] = None


class PublicacionEncontradoResponse(PublicacionEncontradoBase):
    """Esquema de respuesta pública con los datos completos de la publicación de hallazgo."""

    publicacionEncontrado_id: UUID
    usuario_id: UUID
    estado: EstadoPublicacion
    fecha_publicacion: datetime
    motivo_rechazo: Optional[str] = None
    eliminacion_solicitada: bool
    fecha_edicion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
