import uuid
import enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, ForeignKey, String, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from src.database.config import Base
from src.entities.Enums import EstadoReclamo


class EstadoReclamo(str, enum.Enum):
    """Enumerador para los diferentes estados de un reclamo."""

    PENDIENTE = "PENDIENTE"
    EN_REVISION = "EN_REVISION"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"


class Reclamo(Base):
    """
    Entidad que representa un reclamo realizado por un usuario
    sobre un objeto en custodia.

    Attributes:
        reclamo_id (UUID): Identificador único del reclamo (Primary Key).
        objetoEnCustodia_id (UUID): ID del objeto reclamado (Foreign Key).
        usuario_id (UUID): ID del usuario que hace el reclamo (Foreign Key).
        estado (EstadoReclamo): Estado actual del reclamo.
        evidencia_url (str, opcional): Foto de soporte opcional.
        fecha_envio (datetime): Fecha y hora en la que se envió el reclamo.
        fecha_revision (datetime, opcional): Fecha en la que fue revisado.
        motivo_rechazo (str, opcional): Explicación si el reclamo es rechazado.
        fecha_cita (datetime, opcional): Fecha agendada para la entrega.
        horario_cita (str, opcional): Bloque horario de la cita.
        es_presencial (bool): Modo de contingencia (sin dispositivo móvil).
    """

    __tablename__ = "reclamos"

    reclamo_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    objetoEnCustodia_id = Column(
        UUID(as_uuid=True),
        ForeignKey("objetos_en_custodia.objetoEnCustodia_id"),
        nullable=False,
    )
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "usuarios.usuario_id"
        ),  # Ajusta el nombre de la tabla si es distinto
        nullable=False,
    )
    estado = Column(
        Enum(EstadoReclamo), nullable=False, default=EstadoReclamo.PENDIENTE
    )
    evidencia_url = Column(String(500), nullable=True)
    fecha_envio = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_revision = Column(DateTime, nullable=True)
    motivo_rechazo = Column(String(500), nullable=True)
    fecha_cita = Column(DateTime, nullable=True)
    horario_cita = Column(String(150), nullable=True)
    es_presencial = Column(Boolean, nullable=False, default=False)

    # Relaciones (opcionales pero recomendadas basadas en tu ejemplo)
    # objeto = relationship("ObjetoEnCustodia", back_populates="reclamos")
    # usuario = relationship("Usuario", back_populates="reclamos")
