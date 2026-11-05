"""
Autenticación JWT: dependencia reutilizable para rutas protegidas.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.config import Settings, get_settings
from src.core.auditoria import set_actor
from src.database.config import get_db

from src.entities.Sede import Sede
from src.entities.TokenRevocado import TokenRevocado
from src.entities.Usuario import Usuario

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """Claims del usuario autenticado, usados por las rutas protegidas."""

    id_usuario: UUID
    correo: str
    rol: str
    # ADMIN: su sede asignada. SUPERADMIN: la sede que eligió supervisar mediante
    # la cabecera X-Sede-Id (None si no eligió ninguna).
    sede_id: UUID | None = None
    celular: str | None = None


def create_access_token(
    *,
    subject: UUID,
    correo: str,
    rol: str,
    settings: Settings,
    type: str = "access",
    nombre_completo: str | None = None,
    sede_id: UUID | None = None,
) -> str:
    """Genera un JWT de acceso (HS256) con expiración configurada."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict = {
        "sub": str(subject),
        "correo": correo,
        "rol": rol,
        "type": type,
        "iat": int(now.timestamp()),
        "exp": expire,
    }
    if nombre_completo is not None:
        payload["nombre_completo"] = nombre_completo
    if sede_id is not None:
        payload["sede_id"] = str(sede_id)
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    *,
    subject: UUID,
    settings: Settings,
) -> str:
    """Genera un JWT para renovar el token de acceso."""

    now = datetime.now(timezone.utc)

    expire = now + timedelta(days=settings.refresh_token_expire_days)

    payload = {
        "sub": str(subject),
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def hash_token(token: str) -> str:
    """SHA-256 del JWT: así se identifica un token revocado sin guardarlo."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_revocado(db: Session, token: str) -> bool:
    """True si el token fue invalidado con POST /auth/logout (HU35)."""
    return (
        db.query(TokenRevocado.token_hash)
        .filter(TokenRevocado.token_hash == hash_token(token))
        .first()
        is not None
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
    x_sede_id: Annotated[UUID | None, Header(alias="X-Sede-Id")] = None,
) -> CurrentUser:
    """Valida el Bearer JWT, comprueba usuario activo en BD y devuelve el contexto."""
    settings = get_settings()
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    token = credentials.credentials
    try:
        payload = _decode_token(token, settings)

        if payload.get("type") != "access":
            raise JWTError("Tipo de token inválido")
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Token inválido")
        user_id = UUID(sub)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado",
        ) from None

    if token_revocado(db, token):
        raise HTTPException(status_code=401, detail="Sesión cerrada, inicia sesión de nuevo")

    user = db.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Usuario bloqueado")

    set_actor(user.usuario_id)  # la auditoría automática registra quién hizo el cambio

    sede_activa = user.sede_id
    if user.rol == "SUPERADMIN" and x_sede_id is not None:
        # El superadmin no tiene sede propia: elige cuál supervisar en cada petición.
        # Para el resto de roles la cabecera se ignora (un ADMIN no puede cambiar de sede).
        sede = db.query(Sede).filter(Sede.sede_id == x_sede_id).first()
        if not sede:
            raise HTTPException(status_code=404, detail="La sede indicada no existe")
        sede_activa = sede.sede_id

    return CurrentUser(
        id_usuario=user.usuario_id,
        correo=user.correo,
        rol=user.rol,
        sede_id=sede_activa,
        celular=user.celular,
    )


async def get_current_user_con_celular(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """HU25/CU04: para crear reportes, publicaciones o reclamos el usuario debe
    tener registrado su número de celular. Los administradores quedan exentos
    porque operan en nombre de la oficina."""
    if current_user.rol in ("ADMIN", "SUPERADMIN"):
        return current_user
    if not (current_user.celular or "").strip():
        raise HTTPException(
            status_code=403,
            detail=(
                "Debes registrar tu número de celular en tu perfil "
                "(PUT /usuarios/me) antes de crear reportes, publicaciones o reclamos"
            ),
        )
    return current_user


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
    """Exige un administrador con una sede de trabajo. Úsala en endpoints donde
    solo se debe operar sobre los datos de UNA sede.

    - ADMIN: su sede asignada.
    - SUPERADMIN: la sede que eligió con la cabecera `X-Sede-Id`.
    """
    if current_admin.sede_id is None:
        if current_admin.rol == "SUPERADMIN":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Selecciona la sede que vas a supervisar "
                    "(envía la cabecera X-Sede-Id)"
                ),
            )
        raise HTTPException(
            status_code=403,
            detail="El administrador no tiene una sede asignada",
        )
    return current_admin
