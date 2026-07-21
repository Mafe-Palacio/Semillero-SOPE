import uuid
from sqlalchemy.dialects.postgresql import UUID
from src.database.config import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String


class Sede(Base):
    __tablename__ = "sedes"

    sede_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    nombre = Column(String(100), nullable=False)
    codigo = Column(String(50), nullable=False)
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
    ubicaciones = relationship("Ubicacion", back_populates="sede")
    puntos_entrega = relationship("PuntoEntrega", back_populates="sede")
    usuarios_administradores = relationship(
        "Usuario",
        back_populates="sede",
        foreign_keys="Usuario.sede_id",
    )
