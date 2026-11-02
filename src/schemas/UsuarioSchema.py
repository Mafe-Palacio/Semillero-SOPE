from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from src.utils.security import validate_password_strength


class RolUsuario(str, Enum):
    """Roles del sistema para control de acceso."""

    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    USER = "USER"


class TipoVinculacion(str, Enum):
    """Tipos de vinculación con la institución."""

    ESTUDIANTE = "ESTUDIANTE"
    PROFESOR = "PROFESOR"
    ADMINISTRATIVO = "ADMINISTRATIVO"
    OFICIOS_VARIOS = "OFICIOS_VARIOS"


class UsuarioBase(BaseModel):
    """Información básica de identificación del usuario."""

    nombre_completo: str
    cedula: str
    tipo_vinculacion: TipoVinculacion


class UsuarioUpdate(BaseModel):
    """Campos editables por el propio usuario desde su perfil (HU23)."""

    celular: Optional[str] = None
    carnet: Optional[str] = None


class UsuarioAdminUpdate(BaseModel):
    """Campos de moderación exclusivos del rol ADMIN (HU06): bloqueo y sede."""

    is_blocked: Optional[bool] = None
    motivo_bloqueo: Optional[str] = None
    sede_id: Optional[UUID] = None


class UsuarioAdminEdit(BaseModel):
    """Corrección administrativa de datos de identificación de OTRO usuario.
    Separado de UsuarioAdminUpdate porque su propósito es distinto: aquí se
    corrigen datos mal digitados, no se modera el acceso a la cuenta."""

    nombre_completo: Optional[str] = None
    tipo_vinculacion: Optional[TipoVinculacion] = None
    celular: Optional[str] = None
    carnet: Optional[str] = None


class CambiarPasswordRequest(BaseModel):
    """Payload para que el propio usuario cambie su contraseña (PUT /usuarios/me/password)."""

    password_actual: str
    password_nueva: str

    @field_validator("password_nueva")
    @classmethod
    def password_nueva_valida(cls, v: str) -> str:
        es_valida, mensaje = validate_password_strength(v)
        if not es_valida:
            raise ValueError(mensaje)
        return v


class UsuarioResponse(UsuarioBase):
    """Esquema de respuesta pública para los datos de un usuario."""

    usuario_id: UUID
    carnet: Optional[str] = None
    celular: Optional[str] = None
    correo: EmailStr
    rol: RolUsuario
    sede_id: Optional[UUID] = None
    is_verified: bool
    is_active: bool
    is_blocked: bool
    motivo_bloqueo: Optional[str] = None
    fecha_creacion: datetime
    fecha_edicion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ConteoPorEstado(BaseModel):
    """Cantidad total de registros y su desglose por estado."""

    total: int = 0
    por_estado: dict[str, int] = {}


class UsuarioResumen(UsuarioResponse):
    """Usuario con su actividad, para el módulo "Usuarios" del sitio administrativo.

    - reportes_perdida: objetos que el usuario reportó como perdidos.
    - publicaciones_encontradas: objetos que el usuario dice haber encontrado.
    - reclamos: reclamos que ha iniciado sobre objetos en custodia.
    """

    reportes_perdida: ConteoPorEstado = ConteoPorEstado()
    publicaciones_encontradas: ConteoPorEstado = ConteoPorEstado()
    reclamos: ConteoPorEstado = ConteoPorEstado()


class AdminCreate(BaseModel):
    """Alta de un administrador por parte de un SUPERADMIN."""

    nombre_completo: str
    cedula: str
    correo: EmailStr
    tipo_vinculacion: TipoVinculacion = TipoVinculacion.ADMINISTRATIVO
    celular: Optional[str] = None
    sede_id: Optional[UUID] = None
    password_temporal: str

    @field_validator("correo")
    @classmethod
    def correo_institucional(cls, v: str) -> str:
        if not v.lower().endswith("itm.edu.co"):
            raise ValueError("El correo del administrador debe ser institucional (itm.edu.co)")
        return v.lower()

    @field_validator("password_temporal")
    @classmethod
    def password_valida(cls, v: str) -> str:
        es_valida, mensaje = validate_password_strength(v)
        if not es_valida:
            raise ValueError(mensaje)
        return v
