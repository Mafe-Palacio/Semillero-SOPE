from datetime import date, datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from src.entities.PublicacionEncontrado import PublicacionEncontrado
from src.entities.Ubicacion import Ubicacion
from src.entities.PuntoEntrega import PuntoEntrega


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

    def obtener_publicaciones_encontradas_por_sede_hallazgo(
        self, sede_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[PublicacionEncontrado]:
        """
        Publicaciones cuyo lugar de HALLAZGO pertenece a una sede (join con
        Ubicacion). Para el usuario que busca "¿encontraron algo en mi sede?",
        sin importar a qué oficina fue entregado el objeto.
        """
        return (
            self.db.query(PublicacionEncontrado)
            .join(
                Ubicacion,
                PublicacionEncontrado.lugar_hallazgo_id == Ubicacion.ubicacion_id,
            )
            .filter(Ubicacion.sede_id == sede_id)
            .order_by(PublicacionEncontrado.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_publicaciones_encontradas_por_sede_entrega(
        self, sede_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[PublicacionEncontrado]:
        """
        Publicaciones cuyo PUNTO DE ENTREGA pertenece a una sede (join con
        PuntoEntrega). Para la bandeja de la administradora de esa sede,
        sin importar en qué sede se haya encontrado originalmente el objeto
        (ej. encontrado en Robledo, entregado en Fraternidad).
        """
        return (
            self.db.query(PublicacionEncontrado)
            .join(
                PuntoEntrega,
                PublicacionEncontrado.lugar_entrega_fisica_id
                == PuntoEntrega.puntoEntrega_id,
            )
            .filter(PuntoEntrega.sede_id == sede_id)
            .order_by(PublicacionEncontrado.fecha_publicacion.desc())
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

    def buscar_publicaciones_encontradas_por_sede_hallazgo(
        self,
        sede_id: UUID,
        categoria: Optional[str] = None,
        solo_aprobadas: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PublicacionEncontrado]:
        """
        Búsqueda pública: objetos encontrados en una sede, filtrando en la
        base de datos (no en Python) para que skip/limit paginen correcto.
        """
        query = (
            self.db.query(PublicacionEncontrado)
            .join(
                Ubicacion,
                PublicacionEncontrado.lugar_hallazgo_id == Ubicacion.ubicacion_id,
            )
            .filter(Ubicacion.sede_id == sede_id)
        )
        if solo_aprobadas:
            query = query.filter(PublicacionEncontrado.estado == "APROBADA")
        if categoria:
            query = query.filter(PublicacionEncontrado.categoria == categoria)

        return (
            query.order_by(PublicacionEncontrado.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_publicaciones_encontradas_admin(
        self,
        sede_id: UUID,
        usuario_id: Optional[UUID] = None,
        categoria: Optional[str] = None,
        estado: Optional[str] = None,
        lugar_hallazgo_id: Optional[UUID] = None,
        puntoEntrega_id: Optional[UUID] = None,
        eliminacion_solicitada: Optional[bool] = None,
        fecha_hallazgo_desde: Optional[date] = None,
        fecha_hallazgo_hasta: Optional[date] = None,
        fecha_edicion_desde: Optional[datetime] = None,
        fecha_edicion_hasta: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PublicacionEncontrado]:
        """
        Listado administrativo: `sede_id` SIEMPRE se aplica sobre el punto
        de ENTREGA (join con PuntoEntrega) — es la bandeja de la
        administradora que custodia el objeto, sin importar en qué sede
        se encontró originalmente. El resto de parámetros se combinan
        libremente entre sí (AND).
        """
        query = (
            self.db.query(PublicacionEncontrado)
            .join(
                PuntoEntrega,
                PublicacionEncontrado.lugar_entrega_fisica_id
                == PuntoEntrega.puntoEntrega_id,
            )
            .filter(PuntoEntrega.sede_id == sede_id)
        )

        if usuario_id:
            query = query.filter(PublicacionEncontrado.usuario_id == usuario_id)
        if categoria:
            query = query.filter(PublicacionEncontrado.categoria == categoria)
        if estado:
            query = query.filter(PublicacionEncontrado.estado == estado)
        if lugar_hallazgo_id:
            query = query.filter(
                PublicacionEncontrado.lugar_hallazgo_id == lugar_hallazgo_id
            )
        if puntoEntrega_id:
            query = query.filter(
                PublicacionEncontrado.lugar_entrega_fisica_id == puntoEntrega_id
            )
        if eliminacion_solicitada is not None:
            query = query.filter(
                PublicacionEncontrado.eliminacion_solicitada == eliminacion_solicitada
            )
        if fecha_hallazgo_desde and fecha_hallazgo_hasta:
            query = query.filter(
                PublicacionEncontrado.fecha_hallazgo.between(
                    fecha_hallazgo_desde, fecha_hallazgo_hasta
                )
            )
        if fecha_edicion_desde and fecha_edicion_hasta:
            query = query.filter(
                PublicacionEncontrado.fecha_edicion.between(
                    fecha_edicion_desde, fecha_edicion_hasta
                )
            )

        return (
            query.order_by(PublicacionEncontrado.fecha_publicacion.desc())
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
        hubo_cambios = False

        for key, value in kwargs.items():
            if key in campos_permitidos and value is not None:
                if key in {"categoria", "descripcion"} and not str(value).strip():
                    raise ValueError(f"El campo '{key}' no puede estar vacío.")
                setattr(publicacion, key, value)
                hubo_cambios = True

        if hubo_cambios:
            publicacion.usuario_edita_id = usuario_edita_id
            publicacion.fecha_edicion = datetime.now(timezone.utc)

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
