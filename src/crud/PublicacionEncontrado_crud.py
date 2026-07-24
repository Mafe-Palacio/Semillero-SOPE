from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from src.entities.PublicacionEncontrado import PublicacionEncontrado


class PublicacionEncontradoCRUD:
    """
    CRUD para la gestión de publicaciones de objetos encontrados.
    """

    def __init__(self, db: Session):
        """
        Inicializa el CRUD con una sesión de base de datos.

        Args:
            db (Session): Sesión de SQLAlchemy.
        """
        self.db = db

    def crear_publicacion_encontrada(
        self,
        usuario_id: UUID,
        categoria: str,
        descripcion: str,
        lugar_hallazgo_id: UUID,
        lugar_entrega_fisica_id: UUID,
        fecha_hallazgo: date,
        imagen_url: Optional[str] = None,
    ) -> PublicacionEncontrado:
        """
        Crea una nueva publicación de objeto encontrado en estado PENDIENTE.
        """
        if not usuario_id:
            raise ValueError("El usuario es obligatorio")
        if not categoria:
            raise ValueError("La categoría es obligatoria")
        if not descripcion:
            raise ValueError("La descripción es obligatoria")
        if not lugar_hallazgo_id:
            raise ValueError("El lugar donde se encontró el objeto es obligatorio")
        if not lugar_entrega_fisica_id:
            raise ValueError("El punto de entrega física es obligatorio")
        if not fecha_hallazgo:
            raise ValueError("La fecha de hallazgo es obligatoria")

        publicacion = PublicacionEncontrado(
            usuario_id=usuario_id,
            categoria=categoria,
            descripcion=descripcion,
            lugar_hallazgo_id=lugar_hallazgo_id,
            lugar_entrega_fisica_id=lugar_entrega_fisica_id,
            fecha_hallazgo=fecha_hallazgo,
            imagen_url=imagen_url,
            estado="PENDIENTE",
        )

        self.db.add(publicacion)
        self.db.commit()
        self.db.refresh(publicacion)

        return publicacion

    def obtener_publicacion_encontrada_por_id(
        self, publicacionEncontrado_id: UUID
    ) -> Optional[PublicacionEncontrado]:
        """
        Busca y retorna una publicación por su ID.
        """
        return (
            self.db.query(PublicacionEncontrado)
            .filter(
                PublicacionEncontrado.publicacionEncontrado_id
                == publicacionEncontrado_id
            )
            .first()
        )

    def obtener_publicaciones_encontradas(
        self, skip: int = 0, limit: int = 100
    ) -> List[PublicacionEncontrado]:
        """
        Retorna todas las publicaciones ordenadas por fecha de creación.
        """
        return (
            self.db.query(PublicacionEncontrado)
            .order_by(PublicacionEncontrado.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_publicaciones_encontradas_por_usuario(
        self, usuario_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[PublicacionEncontrado]:
        """
        Obtiene las publicaciones creadas por un usuario específico.
        """
        return (
            self.db.query(PublicacionEncontrado)
            .filter(PublicacionEncontrado.usuario_id == usuario_id)
            .order_by(PublicacionEncontrado.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_publicaciones_encontradas_por_categoria(
        self, categoria: str, skip: int = 0, limit: int = 100
    ) -> List[PublicacionEncontrado]:
        """
        Filtra las publicaciones por su categoría.
        """
        return (
            self.db.query(PublicacionEncontrado)
            .filter(PublicacionEncontrado.categoria == categoria)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_publicaciones_encontradas_por_estado(
        self, estado: str, skip: int = 0, limit: int = 100
    ) -> List[PublicacionEncontrado]:
        """
        Filtra las publicaciones por estado (PENDIENTE, APROBADA, RECHAZADA).
        """
        return (
            self.db.query(PublicacionEncontrado)
            .filter(PublicacionEncontrado.estado == estado)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_publicaciones_encontradas_por_lugar_hallazgo(
        self, lugar_hallazgo_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[PublicacionEncontrado]:
        """
        Filtra las publicaciones por la ubicación física del hallazgo.
        """
        return (
            self.db.query(PublicacionEncontrado)
            .filter(PublicacionEncontrado.lugar_hallazgo_id == lugar_hallazgo_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_publicaciones_encontradas_por_punto_entrega(
        self, puntoEntrega_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[PublicacionEncontrado]:
        """
        Obtiene publicaciones aprobadas asociadas a un punto de entrega específico.
        """
        return (
            self.db.query(PublicacionEncontrado)
            .filter(
                PublicacionEncontrado.lugar_entrega_fisica_id == puntoEntrega_id,
                PublicacionEncontrado.estado == "APROBADA",
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_publicaciones_encontradas_por_rango_fecha(
        self, fecha_inicio: date, fecha_fin: date, skip: int = 0, limit: int = 100
    ) -> List[PublicacionEncontrado]:
        """
        Filtra publicaciones según el rango de fecha en que fue encontrado el objeto.
        """
        return (
            self.db.query(PublicacionEncontrado)
            .filter(
                PublicacionEncontrado.fecha_hallazgo.between(fecha_inicio, fecha_fin)
            )
            .order_by(PublicacionEncontrado.fecha_hallazgo.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_publicaciones_encontradas_por_rango_edicion(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PublicacionEncontrado]:
        """
        Obtiene publicaciones cuya última modificación esté dentro del rango de fechas.
        """
        return (
            self.db.query(PublicacionEncontrado)
            .filter(
                PublicacionEncontrado.fecha_edicion.between(fecha_inicio, fecha_fin)
            )
            .order_by(PublicacionEncontrado.fecha_edicion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_publicaciones_encontradas_por_eliminacion_solicitada(
        self, eliminacion_solicitada: bool = True, skip: int = 0, limit: int = 100
    ) -> List[PublicacionEncontrado]:
        """
        Obtiene la lista de publicaciones con solicitud de eliminación pendiente.
        Uso exclusivo de administración.
        """
        return (
            self.db.query(PublicacionEncontrado)
            .filter(
                PublicacionEncontrado.eliminacion_solicitada == eliminacion_solicitada
            )
            .order_by(PublicacionEncontrado.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def aprobar_publicacion_encontrada(
        self, publicacionEncontrado_id: UUID
    ) -> Optional[PublicacionEncontrado]:
        """
        Cambia el estado de la publicación a APROBADA.
        """
        publicacion = self.obtener_publicacion_encontrada_por_id(
            publicacionEncontrado_id
        )
        if not publicacion:
            return None

        publicacion.estado = "APROBADA"

        self.db.commit()
        self.db.refresh(publicacion)

        return publicacion

    def rechazar_publicacion_encontrada(
        self, publicacionEncontrado_id: UUID, motivo_rechazo: str
    ) -> Optional[PublicacionEncontrado]:
        """
        Cambia el estado a RECHAZADA y registra la razón del rechazo.
        """
        if not motivo_rechazo:
            raise ValueError("El motivo de rechazo es obligatorio")

        publicacion = self.obtener_publicacion_encontrada_por_id(
            publicacionEncontrado_id
        )
        if not publicacion:
            return None

        publicacion.estado = "RECHAZADA"
        publicacion.motivo_rechazo = motivo_rechazo

        self.db.commit()
        self.db.refresh(publicacion)

        return publicacion

    def solicitar_eliminacion_publicacion_encontrada(
        self, publicacionEncontrado_id: UUID
    ) -> Optional[PublicacionEncontrado]:
        """
        Marca la bandera para solicitar la eliminación de la publicación.
        """
        publicacion = self.obtener_publicacion_encontrada_por_id(
            publicacionEncontrado_id
        )
        if not publicacion:
            return None

        publicacion.solicitar_eliminacion()

        self.db.commit()
        self.db.refresh(publicacion)

        return publicacion

    def resolver_solicitud_eliminacion_publicacion(
        self,
        publicacionEncontrado_id: UUID,
        aprobar: bool,
        motivo: Optional[str] = None,
    ) -> Optional[PublicacionEncontrado]:
        """
        Elimina la publicación físicamente si aprobar es True, o cancela la solicitud si es False.
        """
        publicacion = self.obtener_publicacion_encontrada_por_id(
            publicacionEncontrado_id
        )
        if not publicacion:
            return None

        if aprobar:
            self.db.delete(publicacion)
            self.db.commit()
            return None

        publicacion.estado = "APROBADA"
        publicacion.eliminacion_solicitada = False
        publicacion.motivo_rechazo = motivo

        self.db.commit()
        self.db.refresh(publicacion)

        return publicacion

    def editar_publicacion_encontrada(
        self,
        publicacionEncontrado_id: UUID,
        usuario_edita_id: Optional[UUID] = None,
        **kwargs,
    ) -> Optional[PublicacionEncontrado]:
        """
        Actualiza categoría, descripción e imagen_url de la publicación.
        Edición restringida a administradora.
        """
        publicacion = self.obtener_publicacion_encontrada_por_id(
            publicacionEncontrado_id
        )
        if not publicacion:
            return None

        if usuario_edita_id is None:
            raise ValueError("El usuario autenticado es obligatorio")

        campos_permitidos = {"categoria", "descripcion", "imagen_url"}
        for key, value in kwargs.items():
            if key in campos_permitidos and value is not None:
                setattr(publicacion, key, value)

        publicacion.usuario_edita_id = usuario_edita_id

        self.db.commit()
        self.db.refresh(publicacion)

        return publicacion

    def obtener_publicaciones_encontradas_elegibles_para_match(
        self, skip: int = 0, limit: int = 100
    ) -> List[PublicacionEncontrado]:
        """
        Obtiene las publicaciones activas y aprobadas aptas para el algoritmo de coincidencia.
        """
        return (
            self.db.query(PublicacionEncontrado)
            .filter(
                PublicacionEncontrado.estado == "APROBADA",
                PublicacionEncontrado.eliminacion_solicitada.is_(False),
            )
            .order_by(PublicacionEncontrado.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
