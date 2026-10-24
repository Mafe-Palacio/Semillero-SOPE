from uuid import UUID
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from src.entities.AuditoriaLog import AuditLog, AccionAuditoria


# HU10 CA2 / CU21: el historial se consulta siempre de 10 en 10 registros.
TAMANO_PAGINA_AUDITORIA = 10


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

    def obtener_logs_paginados(
        self,
        pagina: int = 1,
        entidad: Optional[str] = None,
        accion: Optional[AccionAuditoria] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
    ) -> Tuple[List[AuditLog], int]:
        """Página de 10 registros (más recientes primero) con filtros opcionales
        por tipo de entidad, acción y rango de fechas. Devuelve (registros, total)."""
        consulta = self.db.query(AuditLog)
        if entidad:
            consulta = consulta.filter(AuditLog.entidad == entidad)
        if accion:
            consulta = consulta.filter(AuditLog.accion == accion)
        if fecha_desde:
            consulta = consulta.filter(
                AuditLog.fecha >= datetime.combine(fecha_desde, datetime.min.time())
            )
        if fecha_hasta:
            consulta = consulta.filter(
                AuditLog.fecha
                < datetime.combine(fecha_hasta + timedelta(days=1), datetime.min.time())
            )
        total = consulta.count()
        registros = (
            consulta.order_by(AuditLog.fecha.desc())
            .offset((max(pagina, 1) - 1) * TAMANO_PAGINA_AUDITORIA)
            .limit(TAMANO_PAGINA_AUDITORIA)
            .all()
        )
        return registros, total

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
