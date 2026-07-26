import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship
from src.database.config import Base


class RespuestaSeguridad(Base):
    """
    Entidad que almacena la respuesta que un usuario proporciona
    a una pregunta de seguridad al momento de hacer un reclamo.

    Attributes:
        respuestaSeguridad_id (UUID): Identificador único de la respuesta (PK).
        reclamo_id (UUID): Identificador del reclamo al que pertenece esta respuesta (FK).
        preguntaSeguridad_id (UUID): Identificador de la pregunta que se está respondiendo (FK).
        respuesta_usuario (str): El texto exacto que ingresó el usuario.
    """

    __tablename__ = "respuestas_seguridad"

    respuestaSeguridad_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reclamo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reclamos.reclamo_id"),
        nullable=False,
    )
    preguntaSeguridad_id = Column(
        UUID(as_uuid=True),
        ForeignKey("preguntas_seguridad.preguntaSeguridad_id"),
        nullable=False,
    )
    respuesta_usuario = Column(String(500), nullable=False)

    # Relaciones sugeridas (opcionales, facilitan consultas complejas después)
    # reclamo = relationship("Reclamo", back_populates="respuestas_seguridad")
    # pregunta = relationship("PreguntaSeguridad", back_populates="respuestas")
