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


class EstadoCustodia(str, Enum):
    """Estados del ciclo de inventario de un objeto en custodia."""

    EN_CUSTODIA = "EN_CUSTODIA"
    POR_VENCER = "POR_VENCER"
    SIN_DUENO_DEFINITIVO = "SIN_DUENO_DEFINITIVO"
    RECLAMADO = "RECLAMADO"


class ObjetoEnCustodiaBase(BaseModel):
    """Información base para registrar un objeto ingresado a custodia."""

    categoria: CategoriaObjeto
    descripcion: str
    lugar_origen_id: UUID
    fecha_ingreso: date
    imagen_url: Optional[str] = None


class ObjetoEnCustodiaCreate(ObjetoEnCustodiaBase):
    """Registrado directamente por la administradora (HU03), o generado
    automáticamente al aprobar una PublicacionEncontrado."""

    publicacionEncontrado_id: Optional[UUID] = None
    detalles_internos: Optional[str] = None


class ObjetoEnCustodiaUpdate(BaseModel):
    """Campos editables por administración (corrección de datos ya
    registrados). El `estado` NO se edita aquí — tiene endpoints propios
    con reglas de negocio (bloquear/liberar/archivar-sin-dueno)."""

    categoria: Optional[CategoriaObjeto] = None
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    detalles_internos: Optional[str] = None


class ObjetoEnCustodiaResponse(ObjetoEnCustodiaBase):
    """Esquema de respuesta administrativo con datos completos del inventario."""

    objetoEnCustodia_id: UUID
    admin_id: UUID
    publicacionEncontrado_id: Optional[UUID] = None
    detalles_internos: Optional[str] = None  # Solo se expone al rol ADMIN
    estado: EstadoCustodia
    fecha_vencimiento_alerta: Optional[date] = None
    en_proceso_validacion: bool
    fecha_creacion: Optional[datetime] = None
    fecha_edicion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ObjetoEnCustodiaPublico(BaseModel):
    """Vista filtrada para el catálogo público (HU01): oculta
    detalles_internos y datos administrativos."""

    objetoEnCustodia_id: UUID
    categoria: CategoriaObjeto
    lugar_origen_id: UUID
    fecha_ingreso: date
    imagen_url: Optional[str] = None
    estado: EstadoCustodia

    model_config = ConfigDict(from_attributes=True)
