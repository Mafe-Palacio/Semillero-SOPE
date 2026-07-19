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

##from src.entities.Usuario import Usuario_App

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """Claims mínimos del usuario autenticado (útil si una ruta necesita el contexto)."""

    id_usuario: UUID
    username: str
    rol: str


def create_access_token(
    *,
    subject: UUID,
    username: str,
    rol: str,
    settings: Settings,
) -> str:
    """Genera un JWT de acceso (HS256) con expiración configurada."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(subject),
        "username": username,
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
        """
    user = db.query(Usuario_App).filter(Usuario_App.id_usuario == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    if not user.estado:
        raise HTTPException(status_code=403, detail="Usuario inactivo")

    return CurrentUser(
        id_usuario=user.id_usuario,
        username=user.username,
        rol=user.rol,)"""
