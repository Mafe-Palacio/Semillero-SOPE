import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, ForeignKey, Integer, Boolean, DateTime
from sqlalchemy.orm import relationship
from src.database.config import Base


class PosibleCoincidencia(Base):
    """
    Entidad que registra las coincidencias (Smart Match) entre un
    objeto reportado como perdido y un objeto en custodia.

    Attributes:
        posibleCoincidencia_id (UUID): Identificador único de la coincidencia (PK).
        objetoEnCustodia_id (UUID): ID del objeto encontrado (FK).
        reportePerdida_id (UUID): ID del reporte de pérdida original (FK).
        usuario_id (UUID): ID del usuario dueño del reporte de pérdida (FK).
        score (int): Puntaje de coincidencia (ej. 2 o 3 parámetros coincidentes).
        notificado (bool): Indica si el usuario ya recibió la alerta de esta coincidencia.
        fecha_deteccion (datetime): Fecha y hora en la que el sistema detectó el match.
    """

    __tablename__ = "posibles_coincidencias"

    posibleCoincidencia_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    objetoEnCustodia_id = Column(
        UUID(as_uuid=True),
        ForeignKey("objetos_en_custodia.objetoEnCustodia_id"),
        nullable=False,
    )
    reportePerdida_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "reportes_perdida.reportePerdida_id"
        ),  # Ajusta si tu tabla se llama distinto
        nullable=False,
    )
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.usuario_id"),
        nullable=False,
    )
    score = Column(Integer, nullable=False)
    notificado = Column(Boolean, nullable=False, default=False)
    fecha_deteccion = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relaciones
    objeto_custodia = relationship("ObjetoEnCustodia")
    reporte_perdida = relationship("ReportePerdida")
    usuario = relationship("Usuario")
