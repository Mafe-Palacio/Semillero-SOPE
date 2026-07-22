import uuid
from sqlalchemy.dialects.postgresql import UUID
from src.database.config import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, String


class PublicacionEncontrado(Base):
    """
    Entidad para publicaciones de objetos hallados por los usuarios (HU17).

    Attributes:
        publicacionEncontrado_id (UUID): Identificador único de la publicación (Primary Key).
        usuario_id (UUID): ID del usuario que reporta el objeto hallado.
        categoria (Enum): Categoría del objeto encontrado.
        descripcion (str): Descripción y características del objeto.
        lugar_hallazgo_id (UUID): ID de la ubicación descriptiva donde se encontró.
        lugar_entrega_fisica_id (UUID): ID del punto de entrega donde se custodia físicamente.
        fecha_hallazgo (date): Fecha en que se encontró el objeto.
        imagen_url (str): URL de la fotografía del objeto.
        estado (Enum): Estado de moderación/gestión de la publicación.
        fecha_publicacion (datetime): Timestamp de creación de la publicación.
        motivo_rechazo (str): Justificación administrativa en caso de rechazo.
        eliminacion_solicitada (bool): Indica si el usuario solicitó eliminar la publicación.
        fecha_edicion (datetime): Timestamp de la última actualización.
        usuario_edita_id (UUID): ID del usuario o administrador que editó el registro.

    Relationships:
        usuario (Usuario): Usuario que reporta el hallazgo.
        lugar_hallazgo (Ubicacion): Zona descriptiva del hallazgo.
        lugar_entrega_fisica (PuntoEntrega): Punto físico de recepción/custodia.
        objeto_en_custodia (ObjetoEnCustodia): Registro de inventario físico derivado (1:1).
    """

    __tablename__ = "publicaciones_encontradas"

    publicacionEncontrado_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    usuario_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.usuario_id"), nullable=False
    )
    categoria = Column(
        Enum(
            "ELECTRONICOS",
            "DOCUMENTOS",
            "ROPA_Y_ACCESORIOS",
            "BOLSOS_Y_MALETAS",
            "LLAVES",
            "LIBROS_Y_UTILES",
            "OTROS",
            name="categoriaobjeto",
        ),
        nullable=False,
    )
    descripcion = Column(String(500), nullable=False)

    lugar_hallazgo_id = Column(
        UUID(as_uuid=True), ForeignKey("ubicaciones.ubicacion_id"), nullable=False
    )
    lugar_entrega_fisica_id = Column(
        UUID(as_uuid=True), ForeignKey("puntos_entrega.puntoEntrega_id"), nullable=False
    )

    fecha_hallazgo = Column(Date, nullable=False)
    imagen_url = Column(String(500), nullable=True)
    estado = Column(
        Enum(
            "PENDIENTE",
            "APROBADA",
            "RECHAZADA",
            "ELIMINACION_PENDIENTE",
            "CERRADA",
            name="estadopublicacion",
        ),
        nullable=False,
        default="PENDIENTE",
    )
    fecha_publicacion = Column(DateTime(timezone=True), server_default=func.now())
    motivo_rechazo = Column(String(500), nullable=True)
    eliminacion_solicitada = Column(Boolean, nullable=False, default=False)

    fecha_edicion = Column(DateTime(timezone=True), onupdate=func.now())
    usuario_edita_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.usuario_id"), nullable=True
    )

    # Relaciones
    usuario = relationship("Usuario", back_populates="publicaciones_encontradas")
    lugar_hallazgo = relationship(
        "Ubicacion", back_populates="publicaciones_encontradas"
    )
    lugar_entrega_fisica = relationship(
        "PuntoEntrega", back_populates="publicaciones_encontradas"
    )
    objeto_en_custodia = relationship(
        "ObjetoEnCustodia", back_populates="publicacion_encontrado", uselist=False
    )

    def es_visible_publicamente(self) -> bool:
        """Verifica si la publicación está aprobada para ser consultada públicamente."""
        return self.estado == "APROBADA"

    def solicitar_eliminacion(self) -> None:
        """Marca la publicación para revisión de eliminación por parte de administración."""
        self.eliminacion_solicitada = True
        self.estado = "ELIMINACION_PENDIENTE"
