from datetime import datetime, timezone
from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from src.entities.PuntoEntrega import PuntoEntrega


class PuntoEntregaCRUD:
    """
    CRUD de la entidad PuntoEntrega.
    """

    def __init__(self, db: Session):
        """
        Inicializa el CRUD con una sesión de base de datos.

        Args:
            db (Session): Sesión de SQLAlchemy.
        """
        self.db = db

    def crear_punto_entrega(
        self,
        sede_id: UUID,
        nombre: str,
        tipo: str,
        activa: bool = True,
        usuario_crea_id: Optional[UUID] = None,
    ) -> PuntoEntrega:
        """
        Crea un nuevo punto de entrega.
        """
        if not sede_id:
            raise ValueError("La sede es obligatoria")
        if not nombre:
            raise ValueError("El nombre del punto de entrega es obligatorio")
        if not tipo:
            raise ValueError("El tipo de punto de entrega es obligatorio")

        punto = PuntoEntrega(
            sede_id=sede_id,
            nombre=nombre,
            tipo=tipo,
            activa=activa,
            usuario_crea_id=usuario_crea_id,
        )

        self.db.add(punto)
        self.db.commit()
        self.db.refresh(punto)

        return punto

    def obtener_punto_entrega_por_id(
        self, puntoEntrega_id: UUID
    ) -> Optional[PuntoEntrega]:
        """
        Obtiene un punto de entrega por su identificador.
        """
        return (
            self.db.query(PuntoEntrega)
            .filter(PuntoEntrega.puntoEntrega_id == puntoEntrega_id)
            .first()
        )

    def obtener_puntos_entrega(
        self, skip: int = 0, limit: int = 100, solo_activos: bool = True
    ) -> List[PuntoEntrega]:
        """
        Obtiene la lista de puntos de entrega con opción de filtrar solo los activos.
        """
        query = self.db.query(PuntoEntrega)
        if solo_activos:
            query = query.filter(PuntoEntrega.activa.is_(True))
        return query.order_by(PuntoEntrega.nombre).offset(skip).limit(limit).all()

    def obtener_puntos_entrega_por_sede(
        self,
        sede_id: UUID,
        skip: int = 0,
        limit: int = 100,
        solo_activos: bool = True,
    ) -> List[PuntoEntrega]:
        """
        Obtiene los puntos de entrega pertenecientes a una sede.
        """
        query = self.db.query(PuntoEntrega).filter(PuntoEntrega.sede_id == sede_id)
        if solo_activos:
            query = query.filter(PuntoEntrega.activa.is_(True))
        return query.order_by(PuntoEntrega.nombre).offset(skip).limit(limit).all()

    def obtener_puntos_entrega_por_tipo(
        self, sede_id: UUID, tipo: str, skip: int = 0, limit: int = 100
    ) -> List[PuntoEntrega]:
        """
        Obtiene los puntos de entrega de una sede filtrados por su tipo.
        """
        return (
            self.db.query(PuntoEntrega)
            .filter(PuntoEntrega.sede_id == sede_id, PuntoEntrega.tipo == tipo)
            .order_by(PuntoEntrega.nombre)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_puntos_entrega_por_nombre(
        self, nombre: str, skip: int = 0, limit: int = 100
    ) -> List[PuntoEntrega]:
        """
        Busca puntos de entrega que contengan el texto ingresado en el nombre.
        """
        return (
            self.db.query(PuntoEntrega)
            .filter(PuntoEntrega.nombre.ilike(f"%{nombre}%"))
            .order_by(PuntoEntrega.nombre)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_puntos_entrega_por_activa(
        self, activa: bool, skip: int = 0, limit: int = 100
    ) -> List[PuntoEntrega]:
        """
        Obtiene puntos de entrega según su estado (activos o inactivos).
        """
        return (
            self.db.query(PuntoEntrega)
            .filter(PuntoEntrega.activa == activa)
            .order_by(PuntoEntrega.nombre)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_puntos_entrega_por_rango_creacion(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PuntoEntrega]:
        """
        Obtiene puntos de entrega creados entre dos fechas.
        """
        return (
            self.db.query(PuntoEntrega)
            .filter(PuntoEntrega.fecha_creacion.between(fecha_inicio, fecha_fin))
            .order_by(PuntoEntrega.fecha_creacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_puntos_entrega_por_rango_edicion(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PuntoEntrega]:
        """
        Obtiene puntos de entrega modificados entre dos fechas.
        """
        return (
            self.db.query(PuntoEntrega)
            .filter(PuntoEntrega.fecha_edicion.between(fecha_inicio, fecha_fin))
            .order_by(PuntoEntrega.fecha_edicion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def actualizar_punto_entrega(
        self,
        puntoEntrega_id: UUID,
        usuario_edita_id: Optional[UUID] = None,
        **kwargs,
    ) -> Optional[PuntoEntrega]:
        """
        Actualiza los datos de un punto de entrega.
        """
        punto = self.obtener_punto_entrega_por_id(puntoEntrega_id)
        if not punto:
            return None

        if usuario_edita_id is None:
            raise ValueError("El usuario autenticado es obligatorio")

        campos_permitidos = {"nombre", "tipo", "activa"}
        hubo_cambios = False

        for key, value in kwargs.items():
            if key in campos_permitidos and value is not None:
                setattr(punto, key, value)
                hubo_cambios = True

        if hubo_cambios:
            punto.usuario_edita_id = usuario_edita_id
            punto.fecha_edicion = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(punto)

        return punto

    def desactivar_punto_entrega(
        self, puntoEntrega_id: UUID, usuario_edita_id: Optional[UUID] = None
    ) -> Optional[PuntoEntrega]:
        """
        Desactiva un punto de entrega cambiando su estado a inactivo.
        """
        return self.actualizar_punto_entrega(
            puntoEntrega_id, usuario_edita_id=usuario_edita_id, activa=False
        )
