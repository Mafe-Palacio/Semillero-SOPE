import enum


class RolUsuario(str, enum.Enum):
    """Roles de acceso y permisos para los usuarios del sistema."""

    ADMIN = "ADMIN"
    USER = "USER"


class TipoVinculacion(str, enum.Enum):
    """Tipo de vinculación institucional del usuario con la organización."""

    ESTUDIANTE = "ESTUDIANTE"
    PROFESOR = "PROFESOR"
    ADMINISTRATIVO = "ADMINISTRATIVO"
    OFICIOS_VARIOS = "OFICIOS_VARIOS"


class TipoCodigoVerificacion(str, enum.Enum):
    """Propósito de los códigos de verificación enviados al usuario."""

    REGISTRO = "REGISTRO"
    RECUPERACION_PASSWORD = "RECUPERACION_PASSWORD"


class CategoriaObjeto(str, enum.Enum):
    """Categorías principales para clasificar objetos perdidos o encontrados."""

    ELECTRONICOS = "ELECTRONICOS"
    DOCUMENTOS = "DOCUMENTOS"
    ROPA_Y_ACCESORIOS = "ROPA_Y_ACCESORIOS"
    BOLSOS_Y_MALETAS = "BOLSOS_Y_MALETAS"
    LLAVES = "LLAVES"
    LIBROS_Y_UTILES = "LIBROS_Y_UTILES"
    OTROS = "OTROS"


class EstadoPublicacion(str, enum.Enum):
    """Estados del ciclo de vida de una publicación de objeto."""

    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    ELIMINACION_PENDIENTE = "ELIMINACION_PENDIENTE"
    CERRADA = "CERRADA"


class TipoUbicacion(str, enum.Enum):
    """Clasificación física de la ubicación donde se halló o perdió un objeto."""

    BLOQUE = "BLOQUE"
    PORTERIA = "PORTERIA"
    ZONA_COMUN = "ZONA_COMUN"
    OTRO = "OTRO"


class TipoPuntoEntrega(str, enum.Enum):
    """Ubicación autorizada para la devolución física de objetos."""

    OFICINA = "OFICINA"
    PORTERIA = "PORTERIA"


class EstadoCustodia(str, enum.Enum):
    """Estado del objeto mientras permanece en la oficina de custodia."""

    EN_CUSTODIA = "EN_CUSTODIA"
    POR_VENCER = "POR_VENCER"
    SIN_DUENO_DEFINITIVO = "SIN_DUENO_DEFINITIVO"
    RECLAMADO = "RECLAMADO"


class EstadoReclamo(str, enum.Enum):
    """Etapas del flujo de reclamación de un objeto por parte de un usuario."""

    ENVIADO = "ENVIADO"
    EN_REVISION = "EN_REVISION"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    LISTO_PARA_RECOGER = "LISTO_PARA_RECOGER"
    CANCELADO_POR_USUARIO = "CANCELADO_POR_USUARIO"
    RECLAMADO = "RECLAMADO"


class AccionAuditoria(str, enum.Enum):
    """Acciones específicas registradas en la bitácora de auditoría."""

    CREAR = "CREAR"
    EDITAR = "EDITAR"
    APROBAR = "APROBAR"
    RECHAZAR = "RECHAZAR"
    ELIMINAR = "ELIMINAR"
    BLOQUEAR = "BLOQUEAR"
    DESBLOQUEAR = "DESBLOQUEAR"
    CAMBIO_ESTADO = "CAMBIO_ESTADO"
