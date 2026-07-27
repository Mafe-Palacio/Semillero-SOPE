"""
POST /auth/registro
POST /auth/verificar-registro
"""

import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.auth import CurrentUser, create_access_token
from src.core.config import get_settings
from src.crud.CodigoVerificacion_crud import CodigoVerificacionCRUD
from src.crud.Usuario_crud import UsuarioCRUD
from src.database.config import get_db
from src.schemas.AuthSchema import (
    RegistroRequest,
    RegistroResponse,
    TokenResponse,
    VerificarRegistroRequest,
)
from src.utils.security import generar_codigo_otp, hash_password

router = APIRouter()

DOMINIOS_POR_TIPO = {
    "ESTUDIANTE": "correo.itm.edu.co",
    "PROFESOR": "correo.itm.edu.co",
    "ADMINISTRATIVO": "itm.edu.co",
}


def _concatenar_dominio(
    tipo_vinculacion: str, dominio_personalizado: str | None
) -> str:
    """Arma el dominio del correo institucional según el tipo de vinculación.

    NOTA (pendiente de confirmar con el ITM): hay profesores registrados con
    @correo.itm.edu.co y otros con @itm.edu.co. Mientras se aclara, se asume
    @correo.itm.edu.co para PROFESOR según la regla original documentada.
    """
    if tipo_vinculacion == "OFICIOS_VARIOS":
        if not dominio_personalizado or not dominio_personalizado.strip():
            raise ValueError(
                "Para 'Oficios varios' debes indicar el dominio de tu correo (lo que va después del @)"
            )
        return dominio_personalizado.strip().lstrip("@")

    dominio = DOMINIOS_POR_TIPO.get(tipo_vinculacion)
    if not dominio:
        raise ValueError("Tipo de vinculación no reconocido")
    return dominio


@router.post(
    "/registro", response_model=RegistroResponse, status_code=status.HTTP_201_CREATED
)
async def registrar_usuario(
    data: RegistroRequest,
    db: Session = Depends(get_db),
):
    """Crea el usuario con is_verified=False y despacha el código OTP de registro."""
    try:
        dominio = _concatenar_dominio(
            data.tipo_vinculacion.value, data.dominio_personalizado
        )
        correo = f"{data.prefijo_correo.strip()}@{dominio}"

        usuario_crud = UsuarioCRUD(db)
        usuario = usuario_crud.crear_usuario(
            nombre_completo=data.nombre_completo,
            cedula=data.cedula,
            correo=correo,
            hashed_password=hash_password(data.password),
            rol="USER",
            tipo_vinculacion=data.tipo_vinculacion.value,
        )

        codigo = generar_codigo_otp()
        CodigoVerificacionCRUD(db).crear_codigo_verificacion(
            usuario_id=usuario.usuario_id,
            codigo=codigo,
            tipo="REGISTRO",
        )

        # TODO: integrar envío real por correo (Notification Dispatcher / SMTP).
        # Se imprime aquí solo para desarrollo local mientras no hay proveedor SMTP conectado.
        print(f"[DEV] Código OTP de registro para {correo}: {codigo}")

        return RegistroResponse(usuario_id=usuario.usuario_id, correo=correo)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar el usuario: {str(e)}",
        )


@router.post("/verificar-registro", response_model=TokenResponse)
async def verificar_registro(
    data: VerificarRegistroRequest,
    db: Session = Depends(get_db),
):
    """Valida el código OTP, activa la cuenta y entrega un token de acceso
    inmediato (evita que el usuario tenga que loguearse aparte tras verificar)."""
    try:
        codigo_crud = CodigoVerificacionCRUD(db)
        usuario_crud = UsuarioCRUD(db)

        es_valido = codigo_crud.validar_codigo_verificacion(
            usuario_id=data.usuario_id, codigo=data.codigo, tipo="REGISTRO"
        )
        if not es_valido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código inválido o expirado",
            )

        usuario = usuario_crud.verificar_usuario(data.usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
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
            detail=f"Error al verificar el registro: {str(e)}",
        )
