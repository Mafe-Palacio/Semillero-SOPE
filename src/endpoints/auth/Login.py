"""
POST /auth/login
"""

import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.auth import create_access_token
from src.core.config import get_settings
from src.crud.Usuario_crud import UsuarioCRUD
from src.database.config import get_db
from src.schemas.AuthSchema import LoginRequest, TokenResponse
from src.utils.security import verify_password

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
        token = create_access_token(
            subject=usuario.usuario_id,
            correo=usuario.correo,
            rol=usuario.rol,
            settings=settings,
        )

        return TokenResponse(access_token=token)

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar sesión: {str(e)}",
        )
