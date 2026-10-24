"""
POST /auth/login
"""

import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.auth import create_access_token, get_current_user, CurrentUser
from src.core.auth import (
    create_access_token,
    create_refresh_token,
)
from src.core.config import get_settings
from src.crud.Usuario_crud import UsuarioCRUD
from src.database.config import get_db
from src.schemas.AuthSchema import LoginRequest, TokenResponse, RefreshRequest
from src.utils.security import verify_password
from uuid import UUID
from jose import JWTError, jwt
from src.entities.Usuario import Usuario

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    try:
        usuario_crud = UsuarioCRUD(db)
        usuario = usuario_crud.obtener_usuario_por_correo(data.correo)

        # Mensaje genérico a propósito: no revelar si el correo existe o no.
        credenciales_invalidas = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
        )

        if not usuario or not verify_password(data.password, usuario.hashed_password):
            raise credenciales_invalidas

        if not usuario.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Debes verificar tu cuenta con el código enviado a tu correo",
            )
        if usuario.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tu cuenta está bloqueada. Motivo: {usuario.motivo_bloqueo or 'no especificado'}",
            )
        if not usuario.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu cuenta está desactivada",
            )

        settings = get_settings()
        access_token = create_access_token(
            subject=usuario.usuario_id,
            correo=usuario.correo,
            rol=usuario.rol,
            settings=settings,
        )

        refresh_token = create_refresh_token(
            subject=usuario.usuario_id,
            settings=settings,
        )

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar sesión: {str(e)}",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    data: RefreshRequest,
    db: Session = Depends(get_db),
):
    settings = get_settings()

    # 1. Validar el Refresh Token
    try:
        payload = jwt.decode(
            data.refresh_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        if payload.get("type") != "refresh":
            raise JWTError("Tipo de token inválido")

        sub = payload.get("sub")
        if not sub:
            raise JWTError("Token sin usuario")

        user_id = UUID(sub)

    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token inválido o expirado",
        ) from None

    # 2. Consultar al usuario en la base de datos
    usuario = db.query(Usuario).filter(Usuario.usuario_id == user_id).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    # 3. Verificar el estado actual de la cuenta
    if not usuario.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta no está verificada",
        )

    if usuario.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta está bloqueada",
        )

    if not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta está desactivada",
        )

    # 4. Crear un Access Token nuevo
    nuevo_access_token = create_access_token(
        subject=usuario.usuario_id,
        correo=usuario.correo,
        rol=usuario.rol,
        settings=settings,
    )

    # 5. Devolver el token nuevo y conservar el Refresh Token
    return TokenResponse(
        access_token=nuevo_access_token,
        refresh_token=data.refresh_token,
    )
