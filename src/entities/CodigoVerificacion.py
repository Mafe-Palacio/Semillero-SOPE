import uuid
from sqlalchemy.dialects.postgresql import UUID
from src.database.config import Base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String


class CodigoVerificacion(Base):
    """
    Entidad que representa un código de verificación temporal (OTP) enviado por correo.

    Attributes:
        codigoVerificacion_id (UUID): Identificador único del código (Primary Key).
        usuario_id (UUID): ID del usuario al que pertenece el código.
        codigo (str): Valor numérico o alfanumérico del OTP generado.
        tipo (Enum): Propósito del código ('REGISTRO', 'RECUPERACION_PASSWORD').
        expira_en (datetime): Timestamp límite para validar el código.
        usado (bool): Estado de consumo del código (True si ya se utilizó).

    Relationships:
        usuario (Usuario): Relación 'muchos a uno' con el usuario titular del código.
    """

    __tablename__ = "codigos_verificacion"

    codigoVerificacion_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    usuario_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.usuario_id"), nullable=False
    )
    codigo = Column(String(50), nullable=False)
    tipo = Column(
        Enum("REGISTRO", "RECUPERACION_PASSWORD", name="tipocodigoverificacion"),
        nullable=False,
    )
    expira_en = Column(DateTime(timezone=True), nullable=False)
    usado = Column(Boolean, nullable=False, default=False)

    # Relaciones
    usuario = relationship("Usuario", back_populates="codigos_verificacion")

    def esta_vigente(self) -> bool:
        """Verifica si el código no ha sido usado y aún no ha alcanzado su tiempo de expiración."""
        return (not self.usado) and datetime.now(timezone.utc) < self.expira_en

    def marcar_usado(self) -> None:
        """Marca el código como utilizado para invalidar reintentos futuros."""
        self.usado = True
