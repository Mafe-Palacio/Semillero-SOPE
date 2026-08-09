import uuid
from sqlalchemy.dialects.postgresql import UUID
from src.database.config import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String


class PuntoEntrega(Base):
    """
    Punto físico oficial donde se reciben y custodian objetos
    (ej. Oficina de Objetos Perdidos, Portería Bloque J). Define a qué sede pertenece
    administrativamente un objeto en custodia.

    Attributes:
        puntoEntrega_id (UUID): Identificador único del punto de entrega (Primary Key).
        sede_id (UUID): Clave foránea que vincula el punto con su sede correspondiente (Sede).
        nombre (str): Nombre del punto físico (ej. 'Oficina de Objetos Perdidos').
        tipo (Enum): Tipo de punto de entrega ('OFICINA', 'PORTERIA').
        activa (bool): Permite activar/desactivar el punto de entrega sin borrar historial.
        fecha_creacion (datetime): Timestamp de creación del registro en el sistema.
        fecha_edicion (datetime): Timestamp de la última modificación del registro.
        id_usuario_crea (UUID): ID del usuario administrador que creó el registro.
        id_usuario_edita (UUID): ID del usuario administrador que realizó la última edición.

    Relationships:
        sede (Sede): Relación 'muchos a uno' con la sede a la cual pertenece este punto.
        publicaciones_encontradas (list[PublicacionEncontrado]): Relación 'uno a muchos' con
            las publicaciones de hallazgos dejadas físicamente en este punto.
        objetos_en_custodia (list[ObjetoEnCustodia]): Relación 'uno a muchos' con los objetos
            ingresados y custodiados en este punto de origen.
    """

    __tablename__ = "puntos_entrega"

    puntoEntrega_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    sede_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sedes.sede_id"),
        nullable=False,
    )

    nombre = Column(String(150), nullable=False)
    tipo = Column(Enum("OFICINA", "PORTERIA", name="tipopuntoentrega"), nullable=False)
    activa = Column(Boolean, nullable=False, default=True)

    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_edicion = Column(DateTime(timezone=True), onupdate=func.now())
    usuario_crea_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.usuario_id"), nullable=True
    )
    usuario_edita_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.usuario_id"), nullable=True
    )

    # Relaciones
    sede = relationship("Sede", back_populates="puntos_entrega")
    publicaciones_encontradas = relationship(
        "PublicacionEncontrado", back_populates="lugar_entrega_fisica"
    )
    objetos_en_custodia = relationship(
        "ObjetoEnCustodia", back_populates="lugar_origen"
    )
