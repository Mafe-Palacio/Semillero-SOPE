import uuid
from sqlalchemy.dialects.postgresql import UUID
from src.database.config import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String


class PreguntaSeguridad(Base):
    """
    Entidad que representa las preguntas de validación creadas por el admin (HU04).

    Attributes:
        preguntaSeguridad_id (UUID): Identificador único de la pregunta (Primary Key).
        objetoEnCustodia_id (UUID): ID del objeto en custodia al que pertenece la pregunta.
        pregunta (str): Texto de la pregunta de verificación.
        respuesta_correcta (str): Respuesta esperada para validar la propiedad del objeto.
        orden (int): Posición o secuencia de la pregunta (1 a 3 por objeto).

    Relationships:
        objeto (ObjetoEnCustodia): Objeto en custodia asociado a la pregunta.
        respuestas (list[RespuestaSeguridad]): Respuestas enviadas por usuarios en sus reclamos.
    """

    __tablename__ = "preguntas_seguridad"

    preguntaSeguridad_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    objetoEnCustodia_id = Column(
        UUID(as_uuid=True),
        ForeignKey("objetos_en_custodia.objetoEnCustodia_id"),
        nullable=False,
    )
    pregunta = Column(String(250), nullable=False)
    respuesta_correcta = Column(String(500), nullable=False)
    orden = Column(Integer, nullable=False)

    # Relaciones
    objeto = relationship("ObjetoEnCustodia", back_populates="preguntas_seguridad")
    respuestas = relationship("RespuestaSeguridad", back_populates="pregunta")

    def validar_respuesta(self, respuesta_usuario: str) -> bool:
        """Compara la respuesta del usuario con la respuesta correcta (case-insensitive e ignorando espacios)."""
        return (
            respuesta_usuario.strip().lower() == self.respuesta_correcta.strip().lower()
        )
