import uuid
from sqlalchemy.dialects.postgresql import UUID
from src.database.config import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import date
from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, String


class ObjetoEnCustodia(Base):
    """
    Entidad que representa un objeto físico ingresado e inventariado en custodia (HU03).

    Attributes:
        objetoEnCustodia_id (UUID): Identificador único del objeto en custodia (Primary Key).
        admin_id (UUID): ID del usuario administrador que registró el ingreso.
        publicacionEncontrado_id (UUID): ID de la publicación de hallazgo vinculada (opcional).
        categoria (Enum): Categoría del objeto en inventario.
        descripcion (str): Descripción visible pública del objeto.
        lugar_origen_id (UUID): ID del punto de entrega donde está resguardado físicamente.
        fecha_ingreso (date): Fecha de recepción e ingreso a la oficina/portería.
        imagen_url (str): URL de la fotografía del objeto.
        detalles_internos (str): Notas y características privadas (solo visible para admins).
        estado (Enum): Estado del ciclo de vida en custodia ('EN_CUSTODIA', 'POR_VENCER', etc.).
        fecha_vencimiento_alerta (date): Fecha límite calculada para alerta de vencimiento.
        en_proceso_validacion (bool): Indica si hay un proceso de reclamación o verificación activo.
        fecha_creacion (datetime): Timestamp de registro en inventario.
        fecha_edicion (datetime): Timestamp de la última modificación.
        usuario_edita_id (UUID): ID del administrador que modificó el registro.

    Relationships:
        admin (Usuario): Administrador responsable del registro.
        publicacion_encontrado (PublicacionEncontrado): Reporte de hallazgo de origen (1:1).
        lugar_origen (PuntoEntrega): Punto físico de custodia e inventario.
        preguntas_seguridad (list[PreguntaSeguridad]): Cuestionario para validar propiedad.
        reclamos (list[Reclamo]): Solicitudes de devolución enviadas por los usuarios.
        posibles_coincidencias (list[PosibleCoincidencia]): Coincidencias con reportes de pérdida.
    """

    __tablename__ = "objetos_en_custodia"

    objetoEnCustodia_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    admin_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.usuario_id"), nullable=False
    )
    publicacionEncontrado_id = Column(
        UUID(as_uuid=True),
        ForeignKey("publicaciones_encontradas.publicacionEncontrado_id"),
        nullable=True,
    )
    categoria = Column(
        Enum(
            "ELECTRONICOS",
            "DOCUMENTOS",
            "ROPA_Y_ACCESORIOS",
            "BOLSOS_Y_MALETAS",
            "LLAVES",
            "LIBROS_Y_UTILES",
            "OTROS",
            name="categoriaobjeto",
        ),
        nullable=False,
    )
    descripcion = Column(String(500), nullable=False)
    lugar_origen_id = Column(
        UUID(as_uuid=True), ForeignKey("puntos_entrega.puntoEntrega_id"), nullable=False
    )
    fecha_ingreso = Column(Date, nullable=False)
    imagen_url = Column(String(500), nullable=True)
    detalles_internos = Column(String(500), nullable=True)  # Solo visible para admin
    estado = Column(
        Enum(
            "EN_CUSTODIA",
            "POR_VENCER",
            "SIN_DUENO_DEFINITIVO",
            "RECLAMADO",
            name="estadocustodia",
        ),
        nullable=False,
        default="EN_CUSTODIA",
    )
    fecha_vencimiento_alerta = Column(Date, nullable=True)
    en_proceso_validacion = Column(Boolean, nullable=False, default=False)

    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_edicion = Column(DateTime(timezone=True), onupdate=func.now())
    usuario_edita_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.usuario_id"), nullable=True
    )

    # Relaciones
    admin = relationship("Usuario", foreign_keys=[admin_id])
    publicacion_encontrado = relationship(
        "PublicacionEncontrado", back_populates="objeto_en_custodia"
    )
    lugar_origen = relationship("PuntoEntrega", back_populates="objetos_en_custodia")
    preguntas_seguridad = relationship("PreguntaSeguridad", back_populates="objeto")
    reclamos = relationship("Reclamo", back_populates="objeto")
    posibles_coincidencias = relationship(
        "PosibleCoincidencia", back_populates="objeto_custodia"
    )

    def esta_disponible_para_reclamo(self) -> bool:
        """Verifica si el objeto está en custodia y libre de validaciones activas para ser reclamado."""
        return self.estado == "EN_CUSTODIA" and not self.en_proceso_validacion

    def bloquear_para_validacion(self) -> None:
        """Bloquea temporalmente el objeto mientras un usuario responde su validación."""
        self.en_proceso_validacion = True

    def liberar_validacion(self) -> None:
        """Libera el bloqueo de validación si el proceso de reclamo no prospera."""
        self.en_proceso_validacion = False

    def calcular_dias_en_custodia(self) -> int:
        """Calcula el total de días transcurridos desde el ingreso del objeto."""
        return (date.today() - self.fecha_ingreso).days

    def tiene_origen_publicacion(self) -> bool:
        """Indica si el registro proviene de una publicación previa hecha por un usuario."""
        return self.publicacionEncontrado_id is not None
