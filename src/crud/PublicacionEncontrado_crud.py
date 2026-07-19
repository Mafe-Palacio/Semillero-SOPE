from datetime import datetime
from uuid import UUID
from typing import List, Optional

from sqlalchemy.orm import Session

from src.entities.PublicacionEncontrado import PublicacionEncontrado


class PublicacionEncontradoCRUD:
    """Crud de la entidad PublicacionEncontrado."""


def __init__(self, db: Session):
    """
    Inicializa el CRUD con una sesión de base de datos.

    Args:
        db (Session): Sesión de SQLAlchemy.
    """
    self.db = db


def crear_publicacion(
    self,
    usuario_id: UUID,
    categoria: str,
    descripcion: str,
    lugar_hallado: str,
    fecha_hallazgo: datetime,
    lugar_entrega: str,
    imagen_url: str,
    estado: str,
    id_usuario_crea: UUID = None,
) -> PublicacionEncontrado:
    """
    Crea una nueva publicación de objeto encontrado.
    """

    if not usuario_id:
        raise ValueError("El usuario es obligatorio")

    if not categoria:
        raise ValueError("La categoría es obligatoria")

    if not descripcion:
        raise ValueError("La descripción es obligatoria")

    if not lugar_hallado:
        raise ValueError("El lugar donde se encontró el objeto es obligatorio")

    if not fecha_hallazgo:
        raise ValueError("La fecha de hallazgo es obligatoria")

    if not lugar_entrega:
        raise ValueError("El lugar de entrega es obligatorio")

    if not imagen_url:
        raise ValueError("La imagen es obligatoria")

    if not estado:
        raise ValueError("El estado es obligatorio")

    if id_usuario_crea is None:
        raise ValueError("El usuario autenticado es obligatorio")

    publicacion = PublicacionEncontrado(
        usuario_id=usuario_id,
        categoria=categoria,
        descripcion=descripcion,
        lugar_hallado=lugar_hallado,
        fecha_hallazgo=fecha_hallazgo,
        lugar_entrega=lugar_entrega,
        imagen_url=imagen_url,
        estado=estado,
        id_usuario_crea=id_usuario_crea,
    )

    self.db.add(publicacion)
    self.db.commit()
    self.db.refresh(publicacion)

    return publicacion


def obtener_publicacion(
    self,
    publicacion_id: UUID,
) -> Optional[PublicacionEncontrado]:
    """
    Obtiene una publicación por su identificador.
    """

    return (
        self.db.query(PublicacionEncontrado)
        .filter(PublicacionEncontrado.PublicacionEncontrado_id == publicacion_id)
        .first()
    )


def obtener_publicaciones(
    self,
    skip: int = 0,
    limit: int = 100,
) -> List[PublicacionEncontrado]:
    """
    Obtiene todas las publicaciones.
    """

    return self.db.query(PublicacionEncontrado).offset(skip).limit(limit).all()


def obtener_publicaciones_por_estado(
    self,
    estado: str,
) -> List[PublicacionEncontrado]:
    """
    Obtiene publicaciones por estado.
    """

    return (
        self.db.query(PublicacionEncontrado)
        .filter(PublicacionEncontrado.estado == estado)
        .all()
    )


def obtener_publicaciones_por_categoria(
    self,
    categoria: str,
) -> List[PublicacionEncontrado]:
    """
    Obtiene publicaciones por categoría.
    """

    return (
        self.db.query(PublicacionEncontrado)
        .filter(PublicacionEncontrado.categoria == categoria)
        .all()
    )


def obtener_publicaciones_por_usuario(
    self,
    usuario_id: UUID,
) -> List[PublicacionEncontrado]:
    """
    Obtiene publicaciones realizadas por un usuario.
    """

    return (
        self.db.query(PublicacionEncontrado)
        .filter(PublicacionEncontrado.usuario_id == usuario_id)
        .all()
    )


def actualizar_publicacion(
    self,
    publicacion_id: UUID,
    id_usuario_edita: UUID = None,
    **kwargs,
) -> Optional[PublicacionEncontrado]:
    """
    Actualiza una publicación.
    """

    publicacion = self.obtener_publicacion(publicacion_id)

    if not publicacion:
        return None

    if id_usuario_edita is None:
        raise ValueError("El usuario autenticado es obligatorio")

    publicacion.id_usuario_edita = id_usuario_edita

    if "fecha_hallazgo" in kwargs and kwargs["fecha_hallazgo"] is not None:
        if not isinstance(kwargs["fecha_hallazgo"], datetime):
            raise ValueError("La fecha de hallazgo debe ser un objeto datetime")

    for key, value in kwargs.items():
        if hasattr(publicacion, key):
            setattr(publicacion, key, value)

    self.db.commit()
    self.db.refresh(publicacion)

    return publicacion


def cambiar_estado_publicacion(
    self,
    publicacion_id: UUID,
    estado: str,
    id_usuario_edita: UUID = None,
) -> Optional[PublicacionEncontrado]:
    """
    Actualiza únicamente el estado de una publicación.
    """

    return self.actualizar_publicacion(
        publicacion_id=publicacion_id,
        estado=estado,
        id_usuario_edita=id_usuario_edita,
    )


def rechazar_publicacion(
    self,
    publicacion_id: UUID,
    motivo_rechazo: str,
    id_usuario_edita: UUID = None,
) -> Optional[PublicacionEncontrado]:
    """
    Rechaza una publicación y registra el motivo.
    """

    return self.actualizar_publicacion(
        publicacion_id=publicacion_id,
        estado="RECHAZADA",
        motivo_rechazo=motivo_rechazo,
        id_usuario_edita=id_usuario_edita,
    )


def solicitar_eliminacion(
    self,
    publicacion_id: UUID,
    motivo: str,
    id_usuario_edita: UUID = None,
) -> Optional[PublicacionEncontrado]:
    """
    Registra una solicitud de eliminación.
    """

    return self.actualizar_publicacion(
        publicacion_id=publicacion_id,
        eliminacionSolicitada=motivo,
        id_usuario_edita=id_usuario_edita,
    )


def eliminar_publicacion(
    self,
    publicacion_id: UUID,
) -> bool:
    """
    Elimina una publicación.
    """

    publicacion = self.obtener_publicacion(publicacion_id)

    if publicacion:
        self.db.delete(publicacion)
        self.db.commit()
        return True

    return False


def obtener_todas_publicaciones(
    self,
    skip: int = 0,
    limit: int = 100,
) -> List[PublicacionEncontrado]:
    """
    Obtiene todas las publicaciones.
    """

    return self.db.query(PublicacionEncontrado).offset(skip).limit(limit).all()
