import uuid
from sqlalchemy.dialects.postgresql import UUID
from src.database.config import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String


class Sede(Base):
    """
    Entidad que representa un campus o sede física de la institución.

    Permite administrar la operación multi-sede del sistema, asociando
    ubicaciones descriptivas, puntos de entrega física y administradores.

    Attributes:
        sede_id (UUID): Identificador único de la sede (Primary Key).
        nombre (str): Nombre de la sede (ej. 'Fraternidad', 'Robledo').
        codigo (str): Código abreviado o nomenclatura de la sede (ej. 'FRA', 'ROB').
        activa (bool): Permite activar/desactivar la sede sin borrar su historial.
        fecha_creacion (datetime): Fecha y hora de creación del registro en el sistema.
        fecha_edicion (datetime): Fecha y hora de la última modificación del registro.
        id_usuario_crea (UUID): ID del usuario administrador que creó la sede.
        id_usuario_edita (UUID): ID del usuario administrador que realizó la última modificación.

    Relationships:
        ubicaciones (list[Ubicacion]): Relación 'uno a muchos' con las zonas/áreas
            descriptivas pertenecientes a esta sede.
        puntos_entrega (list[PuntoEntrega]): Relación 'uno a muchos' con los puntos
            físicos oficiales de recepción y custodia de la sede.
        usuarios_administradores (list[Usuario]): Relación 'uno a muchos' con los
            usuarios administradores asignados a gestionar esta sede.
    """

    __tablename__ = "sedes"

    sede_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    nombre = Column(String(100), nullable=False)
    codigo = Column(String(50), nullable=False)
    activa = Column(Boolean, nullable=False, default=True)

    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_edicion = Column(DateTime(timezone=True), onupdate=func.now())
    usuario_crea_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.usuario_id"), nullable=True
    )
    usuario_edita_id = Column(
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
