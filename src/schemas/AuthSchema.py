"""
Schemas específicos del flujo de autenticación (/auth/*).

Se mantienen separados de UsuarioSchema.py porque no representan la forma
de la entidad Usuario, sino los contratos de entrada/salida de cada paso
del flujo: registro, verificación OTP, login y recuperación de contraseña.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.schemas.UsuarioSchema import TipoVinculacion
from src.utils.security import validate_password_strength

# Duración de validez de los códigos OTP (registro y recuperación de
# contraseña). Debe coincidir con minutos_expiracion en las llamadas a
# CodigoVerificacionCRUD.crear_codigo_verificacion() de los endpoints.
OTP_EXPIRACION_MINUTOS = 15


class RegistroRequest(BaseModel):
    """Datos que el usuario diligencia para registrarse (HU28).

    El correo institucional completo lo arma el servidor concatenando
    prefijo_correo con el dominio correspondiente a tipo_vinculacion:
      - ESTUDIANTE / PROFESOR -> @correo.itm.edu.co
      - ADMINISTRATIVO        -> @itm.edu.co
      - OFICIOS_VARIOS        -> @{dominio_personalizado}, provisto por el usuario
    """

    nombre_completo: str
    cedula: str
    tipo_vinculacion: TipoVinculacion
    prefijo_correo: str
    dominio_personalizado: Optional[str] = None  # obligatorio solo si OFICIOS_VARIOS
    password: str

    @field_validator("password")
    @classmethod
    def password_valida(cls, v: str) -> str:
        es_valida, mensaje = validate_password_strength(v)
        if not es_valida:
            raise ValueError(mensaje)
        return v


class RegistroResponse(BaseModel):
    """Confirmación de registro pendiente de verificación por OTP."""

    usuario_id: UUID
    correo: str
    mensaje: str = (
        "Registro exitoso. Revisa tu correo institucional para verificar tu cuenta."
    )


class VerificarRegistroRequest(BaseModel):
    """Código OTP que el usuario ingresa para activar su cuenta."""

    usuario_id: UUID
    codigo: str = Field(
        ...,
        description=f"Código de 6 dígitos enviado por correo. Expira a los {OTP_EXPIRACION_MINUTOS} minutos de haberse generado.",
    )


class ReenviarCodigoRegistroRequest(BaseModel):
    """Solicita un nuevo código OTP de registro (ej. el anterior expiró).
    Genera uno nuevo e invalida automáticamente el anterior."""

    correo: str


class LoginRequest(BaseModel):
    correo: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RecuperarPasswordRequest(BaseModel):
    """Solicita el envío de un código de recuperación al correo institucional."""

    correo: str


class ResetearPasswordRequest(BaseModel):
    """Confirma el código de recuperación y establece la nueva contraseña."""

    correo: str
    codigo: str = Field(
        ...,
        description=f"Código de 6 dígitos enviado por correo. Expira a los {OTP_EXPIRACION_MINUTOS} minutos de haberse generado.",
    )
    password_nueva: str

    @field_validator("password_nueva")
    @classmethod
    def password_nueva_valida(cls, v: str) -> str:
        es_valida, mensaje = validate_password_strength(v)
        if not es_valida:
            raise ValueError(mensaje)
        return v
