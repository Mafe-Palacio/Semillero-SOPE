import uuid
from sqlalchemy.dialects.postgresql import UUID
from src.database.config import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, String, Time


class ReportePerdida(Base):
    """
    Entidad para publicaciones de objetos extraviados por los usuarios (HU18).

    Attributes:
        reportePerdida_id (UUID): Identificador único del reporte (Primary Key).
        usuario_id (UUID): ID del usuario que publica el reporte.
        categoria (Enum): Categoría del objeto extraviado.
        descripcion (str): Detalles y características físicas del objeto.
        lugar_perdida_id (UUID): ID de la ubicación estimada del extravío.
        fecha_perdida (date): Fecha en que se extravió el objeto.
        hora_aproximada (time): Hora estimada del incidente.
        imagen_url (str): URL de la fotografía de referencia.
        estado (Enum): Estado de moderación/gestión del reporte.
        fecha_publicacion (datetime): Timestamp de registro de la publicación.
        motivo_rechazo (str): Justificación en caso de rechazo administrativo.
        eliminacion_solicitada (bool): Indica si el usuario solicitó borrar el reporte.
        fecha_edicion (datetime): Timestamp de la última modificación.
        usuario_edita_id (UUID): ID del usuario o administrador que modificó el registro.

    Relationships:
        usuario (Usuario): Usuario creador del reporte.
        lugar_perdida (Ubicacion): Zona/ubicación donde se presume la pérdida.
        posibles_coincidencias (list[PosibleCoincidencia]): Coincidencias detectadas con hallazgos.
    """

    __tablename__ = "reportes_perdida"

    reportePerdida_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

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
    lugar_perdida_id = Column(
        UUID(as_uuid=True), ForeignKey("ubicaciones.ubicacion_id"), nullable=False
    )
    fecha_perdida = Column(Date, nullable=False)
    hora_aproximada = Column(Time, nullable=True)
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
    usuario = relationship("Usuario", back_populates="reportes_perdida")
    lugar_perdida = relationship("Ubicacion", back_populates="reportes_perdida")
    posibles_coincidencias = relationship(
        "PosibleCoincidencia", back_populates="reporte_perdida"
    )

    def es_elegible_para_match(self) -> bool:
        """Verifica si el reporte está activo y aprobado para cruce de coincidencias."""
        return self.estado == "APROBADA" and not self.eliminacion_solicitada

    def solicitar_eliminacion(self) -> None:
        """Marca el reporte para revisión de eliminación por parte de administración."""
        self.eliminacion_solicitada = True
        self.estado = "ELIMINACION_PENDIENTE"
