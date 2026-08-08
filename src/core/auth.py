"""
Autenticación JWT: dependencia reutilizable para rutas protegidas.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.config import Settings, get_settings
from src.database.config import get_db

from src.entities.Usuario import Usuario

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """Claims del usuario autenticado, usados por las rutas protegidas."""

    id_usuario: UUID
    correo: str
    rol: str
    sede_id: UUID | None = None  # solo tiene valor si rol == ADMIN


def create_access_token(
    *,
    subject: UUID,
    correo: str,
    rol: str,
    settings: Settings,
) -> str:
    """Genera un JWT de acceso (HS256) con expiración configurada."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(subject),
        "correo": correo,
        "rol": rol,
        "iat": int(now.timestamp()),
        "exp": expire,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def _decode_token(token: str, settings: Settings) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> CurrentUser:
    """Valida el Bearer JWT, comprueba usuario activo en BD y devuelve el contexto."""
    settings = get_settings()
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    token = credentials.credentials
    try:
        payload = _decode_token(token, settings)
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Token inválido")
        user_id = UUID(sub)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado",
        ) from None

    user = db.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Usuario bloqueado")

    return CurrentUser(
        id_usuario=user.usuario_id,
        correo=user.correo,
        rol=user.rol,
        sede_id=user.sede_id,
    )


async def get_current_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Exige rol ADMIN o SUPERADMIN. Úsala en cualquier endpoint de escritura
    administrativa: SUPERADMIN hereda todos los permisos de ADMIN."""
    if current_user.rol not in ("ADMIN", "SUPERADMIN"):
        raise HTTPException(status_code=403, detail="Requiere rol de administrador")
    return current_user


async def get_current_superadmin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Exige rol SUPERADMIN exclusivamente. Úsala en endpoints donde ni
    siquiera un ADMIN normal debe poder actuar — ej. reasignar la sede de
    otro admin, o administrar cuentas de otros administradores."""
    if current_user.rol != "SUPERADMIN":
        raise HTTPException(
            status_code=403, detail="Requiere rol de superadministrador"
        )
    return current_user


async def get_current_admin_con_sede(
    current_admin: CurrentUser = Depends(get_current_admin),
) -> CurrentUser:
    """Exige ADMIN con una sede asignada. Úsala en endpoints donde el admin
    solo debe poder operar sobre los datos de SU propia sede."""
    if current_admin.sede_id is None:
        raise HTTPException(
            status_code=403,
            detail="El administrador no tiene una sede asignada",
        )
    return current_admin
