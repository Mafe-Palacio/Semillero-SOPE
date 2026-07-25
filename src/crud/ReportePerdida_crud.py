from datetime import datetime, date, timezone
from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from src.entities.ReportePerdida import ReportePerdida
from src.entities.Ubicacion import Ubicacion


class ReportePerdidaCRUD:
    """
    CRUD para la entidad ReportePerdida.
    """

    def __init__(self, db: Session):
        """
        Inicializa el CRUD con una sesión activa de SQLAlchemy.

        Args:
            db (Session): Sesión de SQLAlchemy.
        """
        self.db = db

    def crear_reporte_perdida(
        self,
        usuario_id: UUID,
        categoria: str,
        descripcion: str,
        lugar_perdida_id: UUID,
        fecha_perdida: date,
        hora_aproximada=None,
        imagen_url: Optional[str] = None,
    ) -> ReportePerdida:
        """
        Registra un nuevo reporte de objeto perdido (estado inicial PENDIENTE).
        """
        if not usuario_id:
            raise ValueError("El usuario es obligatorio")
        if not categoria or not categoria.strip():
            raise ValueError("La categoría es obligatoria")
        if not descripcion or not descripcion.strip():
            raise ValueError("La descripción es obligatoria")
        if not lugar_perdida_id:
            raise ValueError("El lugar donde se perdió el objeto es obligatorio")
        if not fecha_perdida:
            raise ValueError("La fecha de pérdida es obligatoria")
        if fecha_perdida > date.today():
            raise ValueError("La fecha de pérdida no puede ser una fecha futura")

        reporte = ReportePerdida(
            usuario_id=usuario_id,
            categoria=categoria.strip(),
            descripcion=descripcion.strip(),
            lugar_perdida_id=lugar_perdida_id,
            fecha_perdida=fecha_perdida,
            hora_aproximada=hora_aproximada,
            imagen_url=imagen_url,
            estado="PENDIENTE",
        )

        self.db.add(reporte)
        self.db.commit()
        self.db.refresh(reporte)

        return reporte

    def obtener_reporte_perdida_por_id(
        self, reporte_perdida_id: UUID
    ) -> Optional[ReportePerdida]:
        """
        Obtiene un reporte de pérdida por su identificador único.
        """
        return (
            self.db.query(ReportePerdida)
            .filter(ReportePerdida.reportePerdida_id == reporte_perdida_id)
            .first()
        )

    def obtener_reportes_perdida(
        self, skip: int = 0, limit: int = 100
    ) -> List[ReportePerdida]:
        """
        Obtiene el listado general de reportes ordenados por fecha de publicación.
        """
        return (
            self.db.query(ReportePerdida)
            .order_by(ReportePerdida.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_reportes_perdida_por_usuario(
        self, usuario_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ReportePerdida]:
        """
        Obtiene los reportes creados por un usuario específico.
        """
        return (
            self.db.query(ReportePerdida)
            .filter(ReportePerdida.usuario_id == usuario_id)
            .order_by(ReportePerdida.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_reportes_perdida_por_estado(
        self, estado: str, skip: int = 0, limit: int = 100
    ) -> List[ReportePerdida]:
        """
        Obtiene los reportes filtrados por estado (PENDIENTE, APROBADA, RECHAZADA...).
        """
        return (
            self.db.query(ReportePerdida)
            .filter(ReportePerdida.estado == estado)
            .order_by(ReportePerdida.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_reportes_perdida_por_categoria(
        self, categoria: str, skip: int = 0, limit: int = 100
    ) -> List[ReportePerdida]:
        """
        Obtiene los reportes filtrados por categoría de objeto.
        """
        return (
            self.db.query(ReportePerdida)
            .filter(ReportePerdida.categoria == categoria)
            .order_by(ReportePerdida.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_reportes_perdida_por_lugar(
        self, lugar_perdida_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ReportePerdida]:
        """
        Obtiene los reportes asociados a una ubicación física.
        """
        return (
            self.db.query(ReportePerdida)
            .filter(ReportePerdida.lugar_perdida_id == lugar_perdida_id)
            .order_by(ReportePerdida.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_reportes_perdida_por_sede(
        self, sede_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ReportePerdida]:
        """
        Obtiene los reportes cuyo lugar de pérdida pertenece a una sede
        (join con Ubicacion, ya que ReportePerdida no guarda sede_id propio).
        """
        return (
            self.db.query(ReportePerdida)
            .join(Ubicacion, ReportePerdida.lugar_perdida_id == Ubicacion.ubicacion_id)
            .filter(Ubicacion.sede_id == sede_id)
            .order_by(ReportePerdida.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_reportes_perdida_por_rango_fecha(
        self, fecha_inicio: date, fecha_fin: date, skip: int = 0, limit: int = 100
    ) -> List[ReportePerdida]:
        """
        Obtiene reportes cuya fecha de pérdida esté dentro de un rango determinado.
        """
        return (
            self.db.query(ReportePerdida)
            .filter(ReportePerdida.fecha_perdida.between(fecha_inicio, fecha_fin))
            .order_by(ReportePerdida.fecha_perdida.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_reportes_perdida_por_rango_edicion(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ReportePerdida]:
        """
        Obtiene reportes cuya última edición se realizó dentro de un rango.
        """
        return (
            self.db.query(ReportePerdida)
            .filter(ReportePerdida.fecha_edicion.between(fecha_inicio, fecha_fin))
            .order_by(ReportePerdida.fecha_edicion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_reportes_perdida_por_eliminacion_solicitada(
        self, eliminacion_solicitada: bool = True, skip: int = 0, limit: int = 100
    ) -> List[ReportePerdida]:
        """
        Obtiene la cola de reportes con solicitud de eliminación pendiente.
        """
        return (
            self.db.query(ReportePerdida)
            .filter(ReportePerdida.eliminacion_solicitada == eliminacion_solicitada)
            .order_by(ReportePerdida.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_reportes_perdida_elegibles_para_match(
        self, skip: int = 0, limit: int = 100
    ) -> List[ReportePerdida]:
        """
        Obtiene únicamente los reportes aprobados y sin solicitud de eliminación activa.
        """
        return (
            self.db.query(ReportePerdida)
            .filter(
                ReportePerdida.estado == "APROBADA",
                ReportePerdida.eliminacion_solicitada.is_(False),
            )
            .order_by(ReportePerdida.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def aprobar_reporte_perdida(
        self, reporte_perdida_id: UUID
    ) -> Optional[ReportePerdida]:
        """
        Aprueba la publicación de un reporte de pérdida.
        """
        reporte = self.obtener_reporte_perdida_por_id(reporte_perdida_id)
        if not reporte:
            return None

        reporte.estado = "APROBADA"

        self.db.commit()
        self.db.refresh(reporte)

        return reporte

    def rechazar_reporte_perdida(
        self, reporte_perdida_id: UUID, motivo_rechazo: str
    ) -> Optional[ReportePerdida]:
        """
        Rechaza la publicación de un reporte especificando el motivo.
        """
        if not motivo_rechazo or not motivo_rechazo.strip():
            raise ValueError("El motivo de rechazo es obligatorio")

        reporte = self.obtener_reporte_perdida_por_id(reporte_perdida_id)
        if not reporte:
            return None

        reporte.estado = "RECHAZADA"
        reporte.motivo_rechazo = motivo_rechazo.strip()

        self.db.commit()
        self.db.refresh(reporte)

        return reporte

    def solicitar_eliminacion_reporte_perdida(
        self, reporte_perdida_id: UUID
    ) -> Optional[ReportePerdida]:
        """
        Marca la solicitud de eliminación a petición del usuario.
        """
        reporte = self.obtener_reporte_perdida_por_id(reporte_perdida_id)
        if not reporte:
            return None

        reporte.solicitar_eliminacion()

        self.db.commit()
        self.db.refresh(reporte)

        return reporte

    def resolver_solicitud_eliminacion_reporte(
        self, reporte_perdida_id: UUID, aprobar: bool, motivo: Optional[str] = None
    ) -> Optional[ReportePerdida]:
        """
        Resuelve la solicitud de eliminación efectuada por el usuario.
        """
        reporte = self.obtener_reporte_perdida_por_id(reporte_perdida_id)
        if not reporte:
            return None

        if aprobar:
            self.db.delete(reporte)
            self.db.commit()
            return None

        reporte.estado = "APROBADA"
        reporte.eliminacion_solicitada = False
        reporte.motivo_rechazo = motivo

        self.db.commit()
        self.db.refresh(reporte)

        return reporte

    def editar_reporte_perdida(
        self,
        reporte_perdida_id: UUID,
        usuario_edita_id: Optional[UUID] = None,
        **kwargs,
    ) -> Optional[ReportePerdida]:
        """
        Edición administrativa de campos permitidos en un reporte (HU07).
        Campos permitidos: `categoria`, `descripcion`, `imagen_url`.
        """
        if usuario_edita_id is None:
            raise ValueError("El usuario autenticado es obligatorio")

        reporte = self.obtener_reporte_perdida_por_id(reporte_perdida_id)
        if not reporte:
            return None

        campos_permitidos = {"categoria", "descripcion", "imagen_url"}
        hubo_cambios = False

        for key, value in kwargs.items():
            if key in campos_permitidos and value is not None:
                if key in {"categoria", "descripcion"} and not str(value).strip():
                    raise ValueError(f"El campo '{key}' no puede estar vacío.")

                setattr(reporte, key, value)
                hubo_cambios = True

        if hubo_cambios:
            reporte.usuario_edita_id = usuario_edita_id
            reporte.fecha_edicion = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(reporte)

        return reporte
