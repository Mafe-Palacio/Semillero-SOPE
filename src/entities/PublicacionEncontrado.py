import uuid
from sqlalchemy.dialects.postgresql import UUID
from src.database.config import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Column, ForeignKey, String, Float, Integer, Date, DateTime


class PublicacionEncontrado(Base):
    __tablename__ = "Publicaciones_encontradas"

    PublicacionEncontrado_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id = Column(
        UUID(as_uuid=True), ForeignKey("Usuarios.usuario_id"), nullable=True
    )
    categoria = Column(String(500), nullable=False)
    descripcion = Column(String(500), nullable=False)
    lugar_hallado = Column(String(100), nullable=False)
    fecha_hallazgo = Column(DateTime(timezone=True), nullable=False)
    lugar_entrega = Column(String(100), nullable=False)
    imagen_url = Column(String(100), nullable=False)
    estado = Column(String(100), nullable=False)
    fecha_publicacion = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    motivo_rechazo = Column(String(500), nullable=True)
    eliminacionSolicitada = Column(String(100), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_edicion = Column(DateTime(timezone=True), onupdate=func.now())
    id_usuario_crea = Column(
        UUID(as_uuid=True), ForeignKey("usuarios_app.id_usuario"), nullable=True
    )

    id_usuario_edita = Column(
        UUID(as_uuid=True), ForeignKey("usuarios_app.id_usuario"), nullable=True
    )
    # Relación con la entidad Usuario

    usuario = relationship("Usuario", back_populates="Publicaciones_encontradas")
