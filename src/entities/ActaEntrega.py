import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, ForeignKey, String, DateTime, Boolean
from src.database.config import Base


class ActaEntrega(Base):
    """
    Entidad que representa el comprobante formal de entrega de un
    objeto en custodia a su reclamante.

    Attributes:
        actaEntrega_id (UUID): Identificador único del acta (PK).
        reclamo_id (UUID): Identificador del reclamo asociado (FK, único 1:1).
        nombre_reclamante (str): Nombre completo de quien recibe el objeto.
        cedula_reclamante (str): Documento de identidad.
        correo_reclamante (str): Correo de contacto.
        celular_reclamante (str): Teléfono de contacto.
        carnet_reclamante (str): Identificador institucional o carnet.
        firma_url (str): URL de la imagen de la firma capturada.
        fecha_hora_entrega (datetime): Momento exacto de la entrega (Automático).
        procesada_por_admin_id (UUID): Administrador que entregó el objeto (FK).
        validacion_verbal (bool): Si la entrega se hizo por contingencia.
    """

    __tablename__ = "actas_entrega"

    actaEntrega_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # unique=True asegura la relación 1 a 1 con Reclamo
    reclamo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reclamos.reclamo_id"),
        nullable=False,
        unique=True,
    )
    nombre_reclamante = Column(String(150), nullable=False)
    cedula_reclamante = Column(String(50), nullable=False)
    correo_reclamante = Column(String(150), nullable=False)
    celular_reclamante = Column(String(20), nullable=False)
    carnet_reclamante = Column(String(100), nullable=False)
    firma_url = Column(String(500), nullable=False)
    fecha_hora_entrega = Column(DateTime, nullable=False, default=datetime.utcnow)

    procesada_por_admin_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "usuarios.usuario_id"
        ),  # Ajusta si tu tabla de usuarios se llama distinto
        nullable=False,
    )
    validacion_verbal = Column(Boolean, nullable=False, default=False)
