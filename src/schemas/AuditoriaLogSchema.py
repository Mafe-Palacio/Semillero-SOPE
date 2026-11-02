from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from src.entities.Enums import AccionAuditoria


class AuditLogBase(BaseModel):
    """Datos base para registrar un evento de auditoría."""

    entidad: str
    entidad_id: UUID
    accion: AccionAuditoria
    usuario_id: UUID
    detalle: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    """Esquema utilizado para insertar un nuevo log."""

    pass
    # No necesitamos esquema Update, los logs son inmutables.


class AuditLogResponse(AuditLogBase):
    """Esquema para devolver la información del log en la API."""

    auditLog_id: UUID
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogDetalleResponse(AuditLogResponse):
    """Registro de auditoría con datos legibles para el sitio administrativo
    (quién, en qué módulo, qué hizo y un resumen en lenguaje natural)."""

    usuario_nombre: Optional[str] = None
    usuario_rol: Optional[str] = None
    modulo: Optional[str] = None
    resumen: Optional[str] = None
