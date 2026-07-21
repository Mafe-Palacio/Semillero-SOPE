import uuid
from sqlalchemy.dialects.postgresql import UUID
from src.database.config import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String


class Ubicacion(Base):
    """
    Entidad que representa una zona o área descriptiva dentro de un campus/sede.

    Zona descriptiva del campus (ej. Bloque J, Cafetería). No implica
    custodia física; solo describe dónde ocurrió un hallazgo o una pérdida.

    Attributes:
        ubicacion_id (UUID): Identificador único de la ubicación (Primary Key).
        sede_id (UUID): Clave foránea que vincula la ubicación con una sede (Sede).
        nombre (str): Nombre descriptivo de la ubicación (ej. 'Bloque J', 'Cafetería').
        tipo (Enum): Tipo/categoría de la ubicación ('BLOQUE', 'PORTERIA', 'ZONA_COMUN', 'OTRO').
        activa (bool): Indica si la ubicación está activa para ser seleccionada.
        fecha_creacion (datetime): Fecha y hora de creación del registro en el sistema.
        fecha_edicion (datetime): Fecha y hora de la última modificación del registro.
        id_usuario_crea (UUID): ID del usuario de rol administrador que creó el registro.
        id_usuario_edita (UUID): ID del usuario de rol administrador que editó el registro.

    Relationships:
        sede (Sede): Relación 'muchos a uno' con la sede a la que pertenece esta ubicación.
        reportes_perdida (list[ReportePerdida]): Relación 'uno a muchos' con los reportes
            de objetos perdidos en esta ubicación.
        publicaciones_encontradas (list[PublicacionEncontrado]): Relación 'uno a muchos'
            con las publicaciones de objetos encontrados en esta ubicación.
    """

    __tablename__ = "ubicaciones"

    ubicacion_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    sede_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sedes.sede_id"),
        nullable=False,
    )
    nombre = Column(String(100), nullable=False)
    tipo = Column(
        Enum("BLOQUE", "PORTERIA", "ZONA_COMUN", "OTRO", name="tipoubicacion"),
        nullable=False,
    )
    activa = Column(Boolean, nullable=False, default=True)

    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_edicion = Column(DateTime(timezone=True), onupdate=func.now())
    id_usuario_crea = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.usuario_id"), nullable=True
    )
    id_usuario_edita = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.usuario_id"), nullable=True
    )

    # Relaciones
    sede = relationship("Sede", back_populates="ubicaciones")
    reportes_perdida = relationship("ReportePerdida", back_populates="lugar_perdida")
    publicaciones_encontradas = relationship(
        "PublicacionEncontrado", back_populates="lugar_hallazgo"
    )
