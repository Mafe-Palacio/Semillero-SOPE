import uuid
from sqlalchemy.dialects.postgresql import UUID
from src.database.config import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String


class Usuario(Base):
    """
    Entidad que representa a los usuarios del sistema (estudiantes, empleados y admins).

    Attributes:
        usuario_id (UUID): Identificador único del usuario (Primary Key).
        nombre_completo (str): Nombre completo del usuario.
        cedula (str): Número de identificación oficial único.
        carnet (str): Código o número de carnet institucional único.
        celular (str): Teléfono de contacto (obligatorio para publicar/reclamar).
        correo (str): Correo institucional único (@correo.itm.edu.co / @itm.edu.co).
        hashed_password (str): Contraseña encriptada.
        rol (Enum): Rol asignado en el sistema ('ADMIN', 'USER').
        tipo_vinculacion (Enum): Tipo de vinculación institucional ('ESTUDIANTE', etc.).
        sede_id (UUID): Sede asignada (solo si rol == ADMIN).
        is_verified (bool): Indica si confirmó su cuenta vía OTP.
        is_active (bool): Estado general de la cuenta.
        is_blocked (bool): Indica si la cuenta fue bloqueada por la administradora.
        motivo_bloqueo (str): Justificación del bloqueo de la cuenta.
        fecha_creacion (datetime): Timestamp de registro en la plataforma.
        fecha_edicion (datetime): Timestamp de la última modificación del perfil.
        id_usuario_edita (UUID): ID del administrador que modificó el usuario.

    Relationships:
        sede (Sede): Sede administrada por el usuario (si aplica).
        codigos_verificacion (list[CodigoVerificacion]): Historial de códigos OTP generados.
        reportes_perdida (list[ReportePerdida]): Reportes de objetos perdidos creados.
        publicaciones_encontradas (list[PublicacionEncontrado]): Publicaciones de objetos hallados.
    """

    __tablename__ = "usuarios"

    usuario_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    nombre_completo = Column(String(150), nullable=False)
    cedula = Column(String(50), nullable=False, unique=True)
    carnet = Column(String(100), nullable=True, unique=True)
    celular = Column(String(20), nullable=True)
    correo = Column(String(150), nullable=False, unique=True)
    hashed_password = Column(String(200), nullable=False)

    rol = Column(Enum("ADMIN", "USER", name="rolusuario"), nullable=False)
    tipo_vinculacion = Column(
        Enum(
            "ESTUDIANTE",
            "PROFESOR",
            "ADMINISTRATIVO",
            "OFICIOS_VARIOS",
            name="tipovinculacion",
        ),
        nullable=False,
    )

    # Solo aplica si rol == ADMIN; define qué sede administra
    sede_id = Column(UUID(as_uuid=True), ForeignKey("sedes.sede_id"), nullable=True)

    is_verified = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_blocked = Column(Boolean, nullable=False, default=False)
    motivo_bloqueo = Column(String(500), nullable=True)

    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_edicion = Column(DateTime(timezone=True), onupdate=func.now())

    id_usuario_edita = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.usuario_id"), nullable=True
    )

    # Relaciones
    sede = relationship(
        "Sede", back_populates="usuarios_administradores", foreign_keys=[sede_id]
    )
    codigos_verificacion = relationship("CodigoVerificacion", back_populates="usuario")
    reportes_perdida = relationship("ReportePerdida", back_populates="usuario")
    publicaciones_encontradas = relationship(
        "PublicacionEncontrado", back_populates="usuario"
    )

    def esta_habilitado(self) -> bool:
        """Solo True si está verificado, activo y no bloqueado simultáneamente."""
        return self.is_verified and self.is_active and not self.is_blocked

    def es_admin(self) -> bool:
        return self.rol == "ADMIN"

    def dominio_correo(self) -> str:
        return self.correo.split("@")[-1] if self.correo else ""
