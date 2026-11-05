from uuid import UUID
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from src.entities.AuditoriaLog import AuditLog, AccionAuditoria
from src.entities.Usuario import Usuario


# HU10 CA2 / CU21: el historial se consulta siempre de 10 en 10 registros.
TAMANO_PAGINA_AUDITORIA = 10


class AuditLogCRUD:
    """Clase para administrar el registro y lectura de las auditorías del sistema."""

    def __init__(self, db: Session):
        self.db = db

    def _filtro_sede(self, sede_id: UUID):
        """Condición para ver solo la auditoría de una sede.

        Un log pertenece a la sede si lo hizo alguien de esa sede (admins) O si la
        entidad afectada es de esa sede (reportes, hallazgos, objetos, reclamos y
        actas). Hace falta lo segundo porque los ciudadanos (rol USER) no tienen
        sede propia: filtrar solo por la sede del actor ocultaría todo lo que ellos
        hacen (reportar, publicar, reclamar)."""
        from src.entities.ActaEntrega import ActaEntrega
        from src.entities.ObjetoEnCustodia import ObjetoEnCustodia
        from src.entities.PublicacionEncontrado import PublicacionEncontrado
        from src.entities.PuntoEntrega import PuntoEntrega
        from src.entities.Reclamos import Reclamo
        from src.entities.ReportePerdida import ReportePerdida
        from src.entities.Ubicacion import Ubicacion

        db = self.db
        reportes = (
            db.query(ReportePerdida.reportePerdida_id)
            .join(Ubicacion, ReportePerdida.lugar_perdida_id == Ubicacion.ubicacion_id)
            .filter(Ubicacion.sede_id == sede_id)
        )
        publicaciones = (
            db.query(PublicacionEncontrado.publicacionEncontrado_id)
            .join(PuntoEntrega, PublicacionEncontrado.lugar_entrega_fisica_id == PuntoEntrega.puntoEntrega_id)
            .filter(PuntoEntrega.sede_id == sede_id)
        )
        objetos = (
            db.query(ObjetoEnCustodia.objetoEnCustodia_id)
            .join(PuntoEntrega, ObjetoEnCustodia.lugar_origen_id == PuntoEntrega.puntoEntrega_id)
            .filter(PuntoEntrega.sede_id == sede_id)
        )
        reclamos = (
            db.query(Reclamo.reclamo_id)
            .filter(Reclamo.objetoEnCustodia_id.in_(objetos.subquery().select()))
        )
        actas = (
            db.query(ActaEntrega.actaEntrega_id)
            .filter(ActaEntrega.reclamo_id.in_(reclamos.subquery().select()))
        )
        actores_de_la_sede = db.query(Usuario.usuario_id).filter(Usuario.sede_id == sede_id)
        return or_(
            AuditLog.usuario_id.in_(actores_de_la_sede.subquery().select()),
            and_(AuditLog.entidad == "ReportePerdida", AuditLog.entidad_id.in_(reportes.subquery().select())),
            and_(AuditLog.entidad == "PublicacionEncontrado", AuditLog.entidad_id.in_(publicaciones.subquery().select())),
            and_(AuditLog.entidad == "ObjetoEnCustodia", AuditLog.entidad_id.in_(objetos.subquery().select())),
            and_(AuditLog.entidad == "Reclamo", AuditLog.entidad_id.in_(reclamos.subquery().select())),
            and_(AuditLog.entidad == "ActaEntrega", AuditLog.entidad_id.in_(actas.subquery().select())),
        )

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

    def _filtrar(
        self,
        entidad: Optional[str] = None,
        accion: Optional[AccionAuditoria] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        entidades: Optional[List[str]] = None,
        usuario_id: Optional[UUID] = None,
        rol_actor: Optional[str] = None,
        sede_id: Optional[UUID] = None,
    ):
        """Consulta base con los filtros de la bitácora (los usa la lista y la exportación)."""
        consulta = self.db.query(AuditLog)
        if entidad:
            consulta = consulta.filter(AuditLog.entidad == entidad)
        if entidades:
            consulta = consulta.filter(AuditLog.entidad.in_(entidades))
        if usuario_id:
            consulta = consulta.filter(AuditLog.usuario_id == usuario_id)
        if rol_actor:
            consulta = consulta.join(
                Usuario, Usuario.usuario_id == AuditLog.usuario_id
            ).filter(Usuario.rol == rol_actor)
        if sede_id:
            consulta = consulta.filter(self._filtro_sede(sede_id))
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
        return consulta

    def obtener_logs_para_exportar(self, limite: int = 10000, **filtros) -> List[AuditLog]:
        """Registros que coinciden con los filtros, sin paginar (tope `limite`), recientes primero."""
        return self._filtrar(**filtros).order_by(AuditLog.fecha.desc()).limit(limite).all()

    def obtener_logs_paginados(
        self,
        pagina: int = 1,
        entidad: Optional[str] = None,
        accion: Optional[AccionAuditoria] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        entidades: Optional[List[str]] = None,
        usuario_id: Optional[UUID] = None,
        rol_actor: Optional[str] = None,
        sede_id: Optional[UUID] = None,
    ) -> Tuple[List[AuditLog], int]:
        """Página de 10 registros (más recientes primero) con filtros opcionales
        por tipo de entidad, acción, sede y rango de fechas. Devuelve (registros, total)."""
        consulta = self._filtrar(
            entidad, accion, fecha_desde, fecha_hasta, entidades, usuario_id, rol_actor, sede_id
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
        self, entidad: str, entidad_id: UUID, sede_id: Optional[UUID] = None
    ) -> List[AuditLog]:
        """Busca toda la historia (trazabilidad) de un registro en particular."""
        consulta = self.db.query(AuditLog).filter(
            AuditLog.entidad == entidad, AuditLog.entidad_id == entidad_id
        )
        if sede_id:
            consulta = consulta.filter(self._filtro_sede(sede_id))
        return consulta.order_by(AuditLog.fecha.asc()).all()
