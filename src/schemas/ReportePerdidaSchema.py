from datetime import date, datetime, time
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator, Field
from src.utils.imagenes import UrlImagen


class CategoriaObjeto(str, Enum):
    """Categorías generales para clasificación de objetos."""

    ELECTRONICOS = "ELECTRONICOS"
    DOCUMENTOS = "DOCUMENTOS"
    ROPA = "ROPA"
    ACCESORIOS = "ACCESORIOS"
    BILLETERAS_Y_MONEDEROS = "BILLETERAS_Y_MONEDEROS"
    BOLSOS_Y_MALETAS = "BOLSOS_Y_MALETAS"
    LLAVES = "LLAVES"
    LIBROS_Y_UTILES = "LIBROS_Y_UTILES"
    TERMOS_Y_CONTENEDORES = "TERMOS_Y_CONTENEDORES"
    CASCOS = "CASCOS"
    OTROS = "OTROS"


class EstadoPublicacion(str, Enum):
    """Estados del ciclo de vida y moderación de una publicación."""

    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    ELIMINACION_PENDIENTE = "ELIMINACION_PENDIENTE"
    CERRADA = "CERRADA"


class ReportePerdidaBase(BaseModel):
    """Información base para registrar el reporte de un objeto extraviado."""

    categoria: CategoriaObjeto
    descripcion: str
    lugar_perdida_id: UUID
    fecha_perdida: date
    hora_aproximada: Optional[time] = None
    imagen_url: Optional[str] = None
    detalle_lugar: Optional[str] = Field(default=None, max_length=200)
    observaciones: Optional[str] = Field(default=None, max_length=500)

    @field_validator("fecha_perdida")
    @classmethod
    def fecha_no_futura(cls, v: date) -> date:
        """Valida que la fecha ingresada no sea superior a la fecha actual."""
        if v > date.today():
            raise ValueError("La fecha de pérdida no puede ser una fecha futura")
        return v


class ReportePerdidaCreate(ReportePerdidaBase):
    """Datos requeridos para crear un reporte de pérdida."""

    imagen_url: UrlImagen = None


class ReportePerdidaUpdate(BaseModel):
    """Campos permitidos para la edición administrativa (HU07)."""

    categoria: Optional[CategoriaObjeto] = None
    descripcion: Optional[str] = None
    imagen_url: UrlImagen = None


class ReportePerdidaModeracion(BaseModel):
    """Usado por la administradora para aprobar/rechazar (HU02)."""

    estado: EstadoPublicacion
    motivo_rechazo: Optional[str] = None


class ReportePerdidaResolverEliminacion(BaseModel):
    """Resuelve la solicitud de eliminación hecha por el usuario dueño del reporte."""

    aprobar: bool
    motivo: Optional[str] = None


class ReportePerdidaSolicitudEliminacion(BaseModel):
    """Cuerpo opcional de la solicitud de baja: el motivo que ve la administración."""

    motivo: Optional[str] = Field(default=None, max_length=500)


class ReportePerdidaResponse(ReportePerdidaBase):
    """Esquema de respuesta pública con los datos completos del reporte de pérdida."""

    reportePerdida_id: UUID
    usuario_id: UUID
    estado: EstadoPublicacion
    fecha_publicacion: datetime
    motivo_rechazo: Optional[str] = None
    eliminacion_solicitada: bool
    motivo_eliminacion: Optional[str] = None
    fecha_edicion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ReportePerdidaPublico(BaseModel):
    """Vista pública de un reporte de pérdida APROBADO: sin datos del dueño."""

    model_config = ConfigDict(from_attributes=True)

    reportePerdida_id: UUID
    categoria: str
    descripcion: str
    lugar_perdida_nombre: Optional[str] = None
    fecha_perdida: date
    imagen_url: Optional[str] = None
