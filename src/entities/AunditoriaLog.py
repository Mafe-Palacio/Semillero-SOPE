import uuid
import enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, ForeignKey, String, DateTime, Enum
from src.database.config import Base
from src.entities.Enums import AccionAuditoria


class AccionAuditoria(str, enum.Enum):
    """Enumerador para estandarizar las acciones registradas en el sistema."""

    CREAR = "CREAR"
    ACTUALIZAR = "ACTUALIZAR"
    ELIMINAR = "ELIMINAR"
    LEER = "LEER"
    # Puedes agregar más acciones específicas si lo necesitas en el futuro


class AuditLog(Base):
    """
    Entidad que registra los eventos y acciones importantes realizados
    por los usuarios en el sistema para mantener trazabilidad.

    Attributes:
        auditLog_id (UUID): Identificador único del registro (PK).
        entidad (str): Nombre de la tabla o módulo afectado (ej. 'Reclamo', 'ActaEntrega').
        entidad_id (UUID): Identificador único del registro que fue afectado.
        accion (AccionAuditoria): Tipo de acción realizada.
        usuario_id (UUID): Identificador del usuario que realizó la acción (FK).
        detalle (str, opcional): Información extra en formato texto o JSON plano.
        fecha (datetime): Momento exacto en que ocurrió la acción.
    """

    __tablename__ = "audit_logs"

    auditLog_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entidad = Column(String(500), nullable=False)
    entidad_id = Column(UUID(as_uuid=True), nullable=False)
    accion = Column(Enum(AccionAuditoria), nullable=False)
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.usuario_id"),
        nullable=False,
    )
    detalle = Column(String(500), nullable=True)
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow)
