"""
Analítica del sitio administrativo (HU12/CU19 dashboard, HU13/CU20 exportación).
Todo está acotado a UNA sede: la del admin, o la que el SUPERADMIN eligió.
"""

from datetime import date, datetime, timezone
from typing import Any, List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.entities.ActaEntrega import ActaEntrega
from src.entities.ObjetoEnCustodia import ObjetoEnCustodia
from src.entities.PublicacionEncontrado import PublicacionEncontrado
from src.entities.PuntoEntrega import PuntoEntrega
from src.entities.Reclamos import Reclamo
from src.entities.ReportePerdida import ReportePerdida
from src.entities.Ubicacion import Ubicacion
from src.entities.Usuario import Usuario

# Tope de filas por archivo: evita agotar la memoria con un rango enorme.
MAX_FILAS_EXPORTACION = 10000

RECURSOS_EXPORTABLES = (
    "entregas",
    "objetos-custodia",
    "reportes-perdida",
    "publicaciones-encontradas",
)


def _v(x: Any) -> Any:
    return getattr(x, "value", x)


def _rango(consulta, columna, desde: Optional[date], hasta: Optional[date]):
    """Filtra por fechas (inclusivas) tanto columnas Date como DateTime."""
    from datetime import timedelta

    from sqlalchemy import DateTime

    es_datetime = isinstance(columna.type, DateTime)

    def _t(d: date):
        return datetime.combine(d, datetime.min.time()) if es_datetime else d

    if desde:
        consulta = consulta.filter(columna >= _t(desde))
    if hasta:
        consulta = consulta.filter(columna < _t(hasta + timedelta(days=1)))
    return consulta


class AnaliticaCRUD:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------ consultas base
    def _objetos(self, sede_id: UUID):
        return (
            self.db.query(ObjetoEnCustodia)
            .join(PuntoEntrega, ObjetoEnCustodia.lugar_origen_id == PuntoEntrega.puntoEntrega_id)
            .filter(PuntoEntrega.sede_id == sede_id)
        )

    def _reportes(self, sede_id: UUID):
        return (
            self.db.query(ReportePerdida)
            .join(Ubicacion, ReportePerdida.lugar_perdida_id == Ubicacion.ubicacion_id)
            .filter(Ubicacion.sede_id == sede_id)
        )

    def _publicaciones(self, sede_id: UUID):
        return (
            self.db.query(PublicacionEncontrado)
            .join(
                PuntoEntrega,
                PublicacionEncontrado.lugar_entrega_fisica_id == PuntoEntrega.puntoEntrega_id,
            )
            .filter(PuntoEntrega.sede_id == sede_id)
        )

    def _reclamos(self, sede_id: UUID):
        return (
            self.db.query(Reclamo)
            .join(
                ObjetoEnCustodia,
                Reclamo.objetoEnCustodia_id == ObjetoEnCustodia.objetoEnCustodia_id,
            )
            .join(PuntoEntrega, ObjetoEnCustodia.lugar_origen_id == PuntoEntrega.puntoEntrega_id)
            .filter(PuntoEntrega.sede_id == sede_id)
        )

    # ------------------------------------------------------------------ dashboard
    def metricas(
        self, sede_id: UUID, desde: Optional[date] = None, hasta: Optional[date] = None
    ) -> dict:
        # Objetos por estado (filtrados por fecha de ingreso a custodia)
        base = _rango(self._objetos(sede_id), ObjetoEnCustodia.fecha_ingreso, desde, hasta)
        por_estado = {"EN_CUSTODIA": 0, "POR_VENCER": 0, "SIN_DUENO_DEFINITIVO": 0, "RECLAMADO": 0}
        filas = base.with_entities(ObjetoEnCustodia.estado, func.count()).group_by(
            ObjetoEnCustodia.estado
        ).all()
        for estado, cantidad in filas:
            por_estado[_v(estado)] = cantidad
        total = sum(por_estado.values())
        reclamados = por_estado["RECLAMADO"]

        # Días promedio entre el ingreso y la entrega (solo objetos ya entregados)
        entregados = (
            _rango(self._objetos(sede_id), ObjetoEnCustodia.fecha_ingreso, desde, hasta)
            .join(Reclamo, Reclamo.objetoEnCustodia_id == ObjetoEnCustodia.objetoEnCustodia_id)
            .join(ActaEntrega, ActaEntrega.reclamo_id == Reclamo.reclamo_id)
            .with_entities(ObjetoEnCustodia.fecha_ingreso, ActaEntrega.fecha_hora_entrega)
            .all()
        )
        dias = [(f.date() - ingreso).days for ingreso, f in entregados]
        promedio = round(sum(dias) / len(dias), 1) if dias else None

        # Categorías con más pérdidas reportadas (sin contar las rechazadas)
        reportes = _rango(
            self._reportes(sede_id).filter(ReportePerdida.estado != "RECHAZADA"),
            ReportePerdida.fecha_perdida,
            desde,
            hasta,
        )
        categorias = (
            reportes.with_entities(ReportePerdida.categoria, func.count())
            .group_by(ReportePerdida.categoria)
            .order_by(func.count().desc())
            .limit(5)
            .all()
        )

        reclamos = {}
        for estado, cantidad in (
            _rango(self._reclamos(sede_id), Reclamo.fecha_envio, desde, hasta)
            .with_entities(Reclamo.estado, func.count())
            .group_by(Reclamo.estado)
            .all()
        ):
            reclamos[_v(estado)] = cantidad

        # Lo que espera a un administrador (estado actual, sin filtro de fechas)
        pendientes = {
            "reportes_perdida": self._reportes(sede_id).filter(ReportePerdida.estado == "PENDIENTE").count(),
            "publicaciones_encontradas": self._publicaciones(sede_id)
            .filter(PublicacionEncontrado.estado == "PENDIENTE")
            .count(),
            "solicitudes_eliminacion": self._reportes(sede_id)
            .filter(ReportePerdida.eliminacion_solicitada.is_(True))
            .count()
            + self._publicaciones(sede_id)
            .filter(PublicacionEncontrado.eliminacion_solicitada.is_(True))
            .count(),
        }

        return {
            "total_objetos": total,
            "objetos_por_estado": por_estado,
            "reclamados": reclamados,
            "sin_reclamar": total - reclamados,
            "sin_dueno_definitivo": por_estado["SIN_DUENO_DEFINITIVO"],
            "porcentaje_devueltos": round(reclamados * 100 / total, 1) if total else 0.0,
            "dias_promedio_custodia": promedio,
            "categorias_mas_perdidas": [
                {"categoria": _v(c), "total": n} for c, n in categorias
            ],
            "reclamos_por_estado": reclamos,
            "pendientes_aprobacion": pendientes,
            "generado_en": datetime.now(timezone.utc),
        }

    # ----------------------------------------------------------------- exportación
    def datos_exportacion(
        self,
        recurso: str,
        sede_id: UUID,
        desde: Optional[date] = None,
        hasta: Optional[date] = None,
        categoria: Optional[str] = None,
        estado: Optional[str] = None,
    ) -> Tuple[List[str], List[Sequence[Any]]]:
        """(columnas, filas) del recurso pedido, con los filtros de CU20."""
        if recurso == "entregas":
            return self._entregas(sede_id, desde, hasta, categoria)
        if recurso == "objetos-custodia":
            q = _rango(self._objetos(sede_id), ObjetoEnCustodia.fecha_ingreso, desde, hasta)
            if categoria:
                q = q.filter(ObjetoEnCustodia.categoria == categoria)
            if estado:
                q = q.filter(ObjetoEnCustodia.estado == estado)
            filas = (
                q.with_entities(
                    ObjetoEnCustodia.fecha_ingreso,
                    ObjetoEnCustodia.categoria,
                    ObjetoEnCustodia.descripcion,
                    PuntoEntrega.nombre,
                    ObjetoEnCustodia.estado,
                    ObjetoEnCustodia.fecha_vencimiento_alerta,
                )
                .order_by(ObjetoEnCustodia.fecha_ingreso.desc())
                .limit(MAX_FILAS_EXPORTACION)
                .all()
            )
            return (
                ["Fecha de ingreso", "Categoría", "Descripción", "Punto de origen", "Estado", "Vence (alerta)"],
                [tuple(f) for f in filas],
            )
        if recurso == "reportes-perdida":
            q = _rango(self._reportes(sede_id), ReportePerdida.fecha_perdida, desde, hasta)
            if categoria:
                q = q.filter(ReportePerdida.categoria == categoria)
            if estado:
                q = q.filter(ReportePerdida.estado == estado)
            filas = (
                q.join(Usuario, ReportePerdida.usuario_id == Usuario.usuario_id)
                .with_entities(
                    ReportePerdida.fecha_perdida,
                    ReportePerdida.categoria,
                    ReportePerdida.descripcion,
                    Ubicacion.nombre,
                    ReportePerdida.estado,
                    Usuario.nombre_completo,
                    ReportePerdida.fecha_publicacion,
                )
                .order_by(ReportePerdida.fecha_perdida.desc())
                .limit(MAX_FILAS_EXPORTACION)
                .all()
            )
            return (
                ["Fecha de pérdida", "Categoría", "Descripción", "Lugar de pérdida", "Estado", "Reportado por", "Fecha de publicación"],
                [tuple(f) for f in filas],
            )
        if recurso == "publicaciones-encontradas":
            q = _rango(self._publicaciones(sede_id), PublicacionEncontrado.fecha_hallazgo, desde, hasta)
            if categoria:
                q = q.filter(PublicacionEncontrado.categoria == categoria)
            if estado:
                q = q.filter(PublicacionEncontrado.estado == estado)
            filas = (
                q.join(Usuario, PublicacionEncontrado.usuario_id == Usuario.usuario_id)
                .join(
                    Ubicacion,
                    PublicacionEncontrado.lugar_hallazgo_id == Ubicacion.ubicacion_id,
                )
                .with_entities(
                    PublicacionEncontrado.fecha_hallazgo,
                    PublicacionEncontrado.categoria,
                    PublicacionEncontrado.descripcion,
                    Ubicacion.nombre,
                    PuntoEntrega.nombre,
                    PublicacionEncontrado.estado,
                    Usuario.nombre_completo,
                    PublicacionEncontrado.fecha_publicacion,
                )
                .order_by(PublicacionEncontrado.fecha_hallazgo.desc())
                .limit(MAX_FILAS_EXPORTACION)
                .all()
            )
            return (
                ["Fecha de hallazgo", "Categoría", "Descripción", "Lugar de hallazgo", "Punto de entrega", "Estado", "Encontrado por", "Fecha de publicación"],
                [tuple(f) for f in filas],
            )
        raise ValueError(f"Recurso desconocido: {recurso}")

    def _entregas(self, sede_id, desde, hasta, categoria):
        """Actas de entrega con los datos del objeto y del reclamo (soporte ante las directivas)."""
        from sqlalchemy.orm import aliased

        admin = aliased(Usuario)
        q = (
            self.db.query(ActaEntrega)
            .join(Reclamo, ActaEntrega.reclamo_id == Reclamo.reclamo_id)
            .join(ObjetoEnCustodia, Reclamo.objetoEnCustodia_id == ObjetoEnCustodia.objetoEnCustodia_id)
            .join(PuntoEntrega, ObjetoEnCustodia.lugar_origen_id == PuntoEntrega.puntoEntrega_id)
            .outerjoin(admin, ActaEntrega.procesada_por_admin_id == admin.usuario_id)
            .filter(PuntoEntrega.sede_id == sede_id)
        )
        q = _rango(q, ActaEntrega.fecha_hora_entrega, desde, hasta)
        if categoria:
            q = q.filter(ObjetoEnCustodia.categoria == categoria)
        filas = (
            q.with_entities(
                ActaEntrega.fecha_hora_entrega,
                ActaEntrega.nombre_reclamante,
                ActaEntrega.cedula_reclamante,
                ActaEntrega.carnet_reclamante,
                ActaEntrega.correo_reclamante,
                ActaEntrega.celular_reclamante,
                ObjetoEnCustodia.descripcion,
                ObjetoEnCustodia.categoria,
                ObjetoEnCustodia.fecha_ingreso,
                ActaEntrega.validacion_verbal,
                admin.nombre_completo,
            )
            .order_by(ActaEntrega.fecha_hora_entrega.desc())
            .limit(MAX_FILAS_EXPORTACION)
            .all()
        )
        columnas = [
            "Fecha y hora de entrega", "Reclamante", "Cédula", "Carné", "Correo", "Celular",
            "Objeto entregado", "Categoría", "Fecha de ingreso", "Días en custodia",
            "Validación verbal", "Procesada por",
        ]
        salida = []
        for f in filas:
            dias = (f[0].date() - f[8]).days if f[0] and f[8] else ""
            salida.append((*f[:9], dias, f[9], f[10]))
        return columnas, salida
