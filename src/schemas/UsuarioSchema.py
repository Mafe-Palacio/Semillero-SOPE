from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr


class RolUsuario(str, Enum):
    """Roles del sistema para control de acceso."""

    ADMIN = "ADMIN"
    USER = "USER"


class TipoVinculacion(str, Enum):
    """Tipos de vinculación con la institución."""

    ESTUDIANTE = "ESTUDIANTE"
    PROFESOR = "PROFESOR"
    ADMINISTRATIVO = "ADMINISTRATIVO"
    OFICIOS_VARIOS = "OFICIOS_VARIOS"


class UsuarioBase(BaseModel):
    """Información básica e de identificación del usuario."""

    nombre_completo: str
    cedula: str
    tipo_vinculacion: TipoVinculacion


class UsuarioCreate(UsuarioBase):
    """Datos necesarios para el registro de un nuevo usuario."""

    prefijo_correo: str
    password: str


class UsuarioUpdate(BaseModel):
    """Campos editables por el propio usuario desde su perfil."""

    celular: Optional[str] = None
    carnet: Optional[str] = None


class UsuarioAdminUpdate(BaseModel):
    """Campos de gestión y moderación exclusivos del rol ADMIN."""

    is_blocked: Optional[bool] = None
    motivo_bloqueo: Optional[str] = None
    sede_id: Optional[UUID] = None


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
    fecha_registro: datetime
    fecha_edicion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
