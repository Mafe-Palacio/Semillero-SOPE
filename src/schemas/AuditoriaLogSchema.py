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
