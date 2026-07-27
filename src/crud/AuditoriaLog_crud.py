from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from src.entities.AuditoriaLog import AuditLog, AccionAuditoria


class AuditLogCRUD:
    """Clase para administrar el registro y lectura de las auditorías del sistema."""

    def __init__(self, db: Session):
        self.db = db

    def crear_log(
        self,
        entidad: str,
        entidad_id: UUID,
        accion: AccionAuditoria,
        usuario_id: UUID,
        detalle: Optional[str] = None,
    ) -> AuditLog:
        """Crea un nuevo registro inmutable de auditoría."""
        nuevo_log = AuditLog(
            entidad=entidad,
            entidad_id=entidad_id,
            accion=accion,
            usuario_id=usuario_id,
            detalle=detalle,
        )
        self.db.add(nuevo_log)
        self.db.commit()
        self.db.refresh(nuevo_log)
        return nuevo_log

    def obtener_logs(self, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """Obtiene un historial paginado de todos los eventos del sistema."""
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.fecha.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_logs_por_entidad(
        self, entidad: str, entidad_id: UUID
    ) -> List[AuditLog]:
        """Busca toda la historia (trazabilidad) de un registro en particular."""
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.entidad == entidad, AuditLog.entidad_id == entidad_id)
            .order_by(AuditLog.fecha.asc())
            .all()
        )
