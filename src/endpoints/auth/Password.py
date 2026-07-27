"""
POST /auth/recuperar-password
POST /auth/resetear-password
"""

import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.crud.CodigoVerificacion_crud import CodigoVerificacionCRUD
from src.crud.Usuario_crud import UsuarioCRUD
from src.database.config import get_db
from src.schemas.AuthSchema import RecuperarPasswordRequest, ResetearPasswordRequest
from src.schemas.schemas import RespuestaAPI
from src.utils.security import generar_codigo_otp, hash_password

router = APIRouter()


@router.post("/recuperar-password", response_model=RespuestaAPI)
async def recuperar_password(
    data: RecuperarPasswordRequest,
    db: Session = Depends(get_db),
):
    """Despacha un código de recuperación al correo si existe una cuenta
    asociada. Responde igual exista o no el correo, para no filtrar
    qué correos están registrados en el sistema."""
    try:
        usuario_crud = UsuarioCRUD(db)
        usuario = usuario_crud.obtener_usuario_por_correo(data.correo)

        if usuario:
            codigo = generar_codigo_otp()
            CodigoVerificacionCRUD(db).crear_codigo_verificacion(
                usuario_id=usuario.usuario_id,
                codigo=codigo,
                tipo="RECUPERACION_PASSWORD",
                minutos_expiracion=15,
            )
            # TODO: integrar envío real por correo (Notification Dispatcher / SMTP).
            print(f"[DEV] Código de recuperación para {data.correo}: {codigo}")

        return RespuestaAPI(
            mensaje="Si el correo está registrado, recibirás un código de recuperación.",
            exito=True,
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la solicitud: {str(e)}",
        )


@router.post("/resetear-password", response_model=RespuestaAPI)
async def resetear_password(
    data: ResetearPasswordRequest,
    db: Session = Depends(get_db),
):
    try:
        usuario_crud = UsuarioCRUD(db)
        usuario = usuario_crud.obtener_usuario_por_correo(data.correo)

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código inválido o expirado",
            )

        codigo_crud = CodigoVerificacionCRUD(db)
        es_valido = codigo_crud.validar_codigo_verificacion(
            usuario_id=usuario.usuario_id,
            codigo=data.codigo,
            tipo="RECUPERACION_PASSWORD",
        )
        if not es_valido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código inválido o expirado",
            )

        usuario_crud.cambiar_password_usuario(
            usuario_id=usuario.usuario_id,
            hashed_password=hash_password(data.password_nueva),
        )

        return RespuestaAPI(mensaje="Contraseña restablecida exitosamente", exito=True)

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al restablecer la contraseña: {str(e)}",
        )
