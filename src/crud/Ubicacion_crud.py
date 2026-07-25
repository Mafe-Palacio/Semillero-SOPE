from datetime import datetime, timezone
from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from src.entities.Ubicacion import Ubicacion


class UbicacionCRUD:
    """
    CRUD de la entidad Ubicacion.
    """

    def __init__(self, db: Session):
        """
        Inicializa el CRUD con una sesión de base de datos.

        Args:
            db (Session): Sesión de SQLAlchemy.
        """
        self.db = db

    def crear_ubicacion(
        self,
        sede_id: UUID,
        nombre: str,
        tipo: str,
        activa: bool = True,
        usuario_crea_id: Optional[UUID] = None,
    ) -> Ubicacion:
        """
        Crea una nueva ubicación.
        """
        if not sede_id:
            raise ValueError("La sede es obligatoria")
        if not nombre:
            raise ValueError("El nombre de la ubicación es obligatorio")
        if not tipo:
            raise ValueError("El tipo de ubicación es obligatorio")

        ubicacion = Ubicacion(
            sede_id=sede_id,
            nombre=nombre,
            tipo=tipo,
            activa=activa,
            usuario_crea_id=usuario_crea_id,
        )

        self.db.add(ubicacion)
        self.db.commit()
        self.db.refresh(ubicacion)

        return ubicacion

    def obtener_ubicacion_por_id(self, ubicacion_id: UUID) -> Optional[Ubicacion]:
        """
        Obtiene una ubicación por su identificador.
        """
        return (
            self.db.query(Ubicacion)
            .filter(Ubicacion.ubicacion_id == ubicacion_id)
            .first()
        )

    def obtener_ubicaciones(
        self, skip: int = 0, limit: int = 100, solo_activas: bool = True
    ) -> List[Ubicacion]:
        """
        Obtiene la lista de ubicaciones con opción de filtrar solo las activas.
        """
        query = self.db.query(Ubicacion)
        if solo_activas:
            query = query.filter(Ubicacion.activa.is_(True))
        return query.order_by(Ubicacion.nombre).offset(skip).limit(limit).all()

    def obtener_ubicaciones_por_sede(
        self,
        sede_id: UUID,
        skip: int = 0,
        limit: int = 100,
        solo_activas: bool = True,
    ) -> List[Ubicacion]:
        """
        Obtiene las ubicaciones pertenecientes a una sede.
        """
        query = self.db.query(Ubicacion).filter(Ubicacion.sede_id == sede_id)
        if solo_activas:
            query = query.filter(Ubicacion.activa.is_(True))
        return query.order_by(Ubicacion.nombre).offset(skip).limit(limit).all()

    def obtener_ubicaciones_por_tipo(
        self,
        tipo: str,
        sede_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Ubicacion]:
        """
        Obtiene ubicaciones filtradas por tipo. Si se indica sede_id,
        filtra además dentro de esa sede.
        """
        query = self.db.query(Ubicacion).filter(Ubicacion.tipo == tipo)
        if sede_id:
            query = query.filter(Ubicacion.sede_id == sede_id)
        return query.order_by(Ubicacion.nombre).offset(skip).limit(limit).all()

    def obtener_ubicaciones_por_nombre(
        self, nombre: str, skip: int = 0, limit: int = 100
    ) -> List[Ubicacion]:
        """
        Busca ubicaciones que contengan el texto ingresado en el nombre.
        """
        return (
            self.db.query(Ubicacion)
            .filter(Ubicacion.nombre.ilike(f"%{nombre}%"))
            .order_by(Ubicacion.nombre)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_ubicaciones_por_activa(
        self, activa: bool, skip: int = 0, limit: int = 100
    ) -> List[Ubicacion]:
        """
        Obtiene ubicaciones según su estado (activas o inactivas).
        """
        return (
            self.db.query(Ubicacion)
            .filter(Ubicacion.activa == activa)
            .order_by(Ubicacion.nombre)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_ubicaciones_por_rango_creacion(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Ubicacion]:
        """
        Obtiene ubicaciones creadas entre dos fechas.
        """
        return (
            self.db.query(Ubicacion)
            .filter(Ubicacion.fecha_creacion.between(fecha_inicio, fecha_fin))
            .order_by(Ubicacion.fecha_creacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_ubicaciones_por_rango_edicion(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Ubicacion]:
        """
        Obtiene ubicaciones modificadas entre dos fechas.
        """
        return (
            self.db.query(Ubicacion)
            .filter(Ubicacion.fecha_edicion.between(fecha_inicio, fecha_fin))
            .order_by(Ubicacion.fecha_edicion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def actualizar_ubicacion(
        self, ubicacion_id: UUID, usuario_edita_id: Optional[UUID] = None, **kwargs
    ) -> Optional[Ubicacion]:
        """
        Actualiza los datos de una ubicación.
        """
        ubicacion = self.obtener_ubicacion_por_id(ubicacion_id)
        if not ubicacion:
            return None

        if usuario_edita_id is None:
            raise ValueError("El usuario autenticado es obligatorio")

        campos_permitidos = {"nombre", "tipo", "activa"}
        hubo_cambios = False

        for key, value in kwargs.items():
            if key in campos_permitidos and value is not None:
                setattr(ubicacion, key, value)
                hubo_cambios = True

        if hubo_cambios:
            ubicacion.usuario_edita_id = usuario_edita_id
            ubicacion.fecha_edicion = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(ubicacion)

        return ubicacion

    def desactivar_ubicacion(
        self, ubicacion_id: UUID, usuario_edita_id: Optional[UUID] = None
    ) -> Optional[Ubicacion]:
        """
        Desactiva una ubicación cambiando su estado a inactivo.
        """
        return self.actualizar_ubicacion(
            ubicacion_id, usuario_edita_id=usuario_edita_id, activa=False
        )
