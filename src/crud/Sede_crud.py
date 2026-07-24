from datetime import datetime, timezone
from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from src.entities.Sede import Sede


class SedeCRUD:
    """
    CRUD de la entidad Sede.
    """

    def __init__(self, db: Session):
        """
        Inicializa el CRUD con una sesión de base de datos.

        Args:
            db (Session): Sesión de SQLAlchemy.
        """
        self.db = db

    def crear_sede(
        self,
        nombre: str,
        codigo: str,
        activa: bool = True,
        usuario_crea_id: Optional[UUID] = None,
    ) -> Sede:
        """
        CRUD de la entidad Sede.
        """
        if not nombre:
            raise ValueError("El nombre de la sede es obligatorio.")

        if not codigo:
            raise ValueError("El código de la sede es obligatorio.")

        if self.obtener_sede_por_codigo(codigo):
            raise ValueError(f"Ya existe una sede con el código '{codigo}'")

        sede = Sede(
            nombre=nombre,
            codigo=codigo,
            activa=activa,
            usuario_crea_id=usuario_crea_id,
        )

        self.db.add(sede)
        self.db.commit()
        self.db.refresh(sede)

        return sede

    def obtener_sede_por_id(self, sede_id: UUID) -> Optional[Sede]:
        """
        Obtiene una sede por su id.
        """
        return self.db.query(Sede).filter(Sede.sede_id == sede_id).first()

    def obtener_sedes(
        self, skip: int = 0, limit: int = 100, solo_activas: bool = False
    ) -> List[Sede]:
        """
        Obtiene la lista de sedes con opción de filtrar solo las activas.
        """
        query = self.db.query(Sede)
        if solo_activas:
            query = query.filter(Sede.activa.is_(True))
        return query.order_by(Sede.nombre).offset(skip).limit(limit).all()

    def obtener_sedes_por_nombre(
        self, nombre: str, skip: int = 0, limit: int = 100
    ) -> List[Sede]:
        """Búsqueda parcial e insensible a mayúsculas (ej. 'frat' encuentra
        'Fraternidad')."""
        return (
            self.db.query(Sede)
            .filter(Sede.nombre.ilike(f"%{nombre}%"))
            .order_by(Sede.nombre)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_sede_por_codigo(self, codigo: str):
        """
        Obtiene una sede por su código.
        """
        return self.db.query(Sede).filter(Sede.codigo == codigo).first()

    def obtener_sedes_por_activa(
        self, activa: bool, skip: int = 0, limit: int = 100
    ) -> List[Sede]:
        """Permite tanto listar activas (activa=True) como inactivas (activa=False)"""
        return (
            self.db.query(Sede)
            .filter(Sede.activa == activa)
            .order_by(Sede.nombre)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_sedes_por_rango_creacion(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Sede]:
        """
        Obtiene una sede por su código.
        """
        return (
            self.db.query(Sede)
            .filter(Sede.fecha_creacion.between(fecha_inicio, fecha_fin))
            .order_by(Sede.fecha_creacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_sedes_por_rango_edicion(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Sede]:
        """
        Obtiene sedes modificadas entre dos fechas.
        """
        return (
            self.db.query(Sede)
            .filter(Sede.fecha_edicion.between(fecha_inicio, fecha_fin))
            .order_by(Sede.fecha_edicion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def actualizar_sede(
        self, sede_id: UUID, usuario_edita_id: Optional[UUID] = None, **kwargs
    ) -> Optional[Sede]:
        """
        Actualiza los datos de una sede.
        """
        sede = self.obtener_sede_por_id(sede_id)
        if not sede:
            return None

        if usuario_edita_id is None:
            raise ValueError("El usuario autenticado es obligatorio")

        campos_permitidos = {"nombre", "codigo", "activa"}
        hubo_cambios = False

        for key, value in kwargs.items():
            if key in campos_permitidos and value is not None:
                setattr(sede, key, value)
                hubo_cambios = True

        if hubo_cambios:
            sede.usuario_edita_id = usuario_edita_id
            sede.fecha_edicion = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(sede)

        return sede

    def desactivar_sede(
        self, sede_id: UUID, usuario_edita_id: Optional[UUID] = None
    ) -> Optional[Sede]:
        """
        Desactiva una sede sin eliminarla cambiando su estado a inactivo.(preserva el historial referenciado).
        """
        return self.actualizar_sede(
            sede_id, usuario_edita_id=usuario_edita_id, activa=False
        )
