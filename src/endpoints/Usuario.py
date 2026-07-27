"""
Endpoint de Usuarios
"""

import traceback
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user, get_current_admin
from src.crud.Usuario_crud import UsuarioCRUD
from src.database.config import get_db
from src.schemas.UsuarioSchema import (
    CambiarPasswordRequest,
    UsuarioAdminEdit,
    UsuarioAdminUpdate,
    UsuarioResponse,
    UsuarioUpdate,
)
from src.schemas.schemas import RespuestaAPI
from src.utils.security import hash_password, verify_password

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"],
    dependencies=[Depends(get_current_user)],
)


# ---------------------------------------------------------------------------
# Perfil propio (cualquier usuario autenticado, sobre sí mismo)
# ---------------------------------------------------------------------------


@router.get("/me", response_model=UsuarioResponse)
async def obtener_mi_perfil(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    crud = UsuarioCRUD(db)
    usuario = crud.obtener_usuario_por_id(current_user.id_usuario)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return usuario


@router.put("/me", response_model=UsuarioResponse)
async def actualizar_mi_perfil(
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Campos editables por el propio usuario (HU23): celular, carnet."""
    try:
        crud = UsuarioCRUD(db)
        return crud.actualizar_perfil_usuario(
            usuario_id=current_user.id_usuario,
            celular=data.celular,
            carnet=data.carnet,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el perfil: {str(e)}",
        )


@router.put("/me/password", response_model=RespuestaAPI)
async def cambiar_mi_password(
    data: CambiarPasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        crud = UsuarioCRUD(db)
        usuario = crud.obtener_usuario_por_id(current_user.id_usuario)

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )

        if not verify_password(data.password_actual, usuario.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña actual no es correcta",
            )

        crud.cambiar_password_usuario(
            usuario_id=current_user.id_usuario,
            hashed_password=hash_password(data.password_nueva),
        )

        return RespuestaAPI(mensaje="Contraseña actualizada exitosamente", exito=True)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cambiar la contraseña: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Gestión administrativa (solo ADMIN) — rutas estáticas antes de /{usuario_id}
# ---------------------------------------------------------------------------


@router.get("/", response_model=List[UsuarioResponse])
async def obtener_todos_usuarios(
    nombre: Optional[str] = Query(None, description="Filtra por nombre parcial"),
    rol: Optional[str] = Query(None, description="Filtra por rol: 'ADMIN' o 'USER'"),
    tipo_vinculacion: Optional[str] = Query(
        None,
        description="'ESTUDIANTE', 'PROFESOR', 'ADMINISTRATIVO', 'OFICIOS_VARIOS'",
    ),
    sede_id: Optional[UUID] = Query(
        None, description="Filtra por sede asignada (solo aplica a ADMIN)"
    ),
    verificado: Optional[bool] = Query(
        None, description="Filtra por correo verificado"
    ),
    activo: Optional[bool] = Query(None, description="Filtra por cuenta activa"),
    bloqueado: Optional[bool] = Query(None, description="Solo usuarios bloqueados"),
    fecha_creacion_desde: Optional[datetime] = Query(None),
    fecha_creacion_hasta: Optional[datetime] = Query(None),
    fecha_edicion_desde: Optional[datetime] = Query(None),
    fecha_edicion_hasta: Optional[datetime] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Listado de usuarios (solo ADMIN, por los datos sensibles que expone).
    Orden de precedencia si mandan varios filtros a la vez:
    rango de creación > rango de edición > bloqueado > verificado > activo
    > rol > tipo_vinculacion > sede > nombre.
    """
    try:
        crud = UsuarioCRUD(db)

        if fecha_creacion_desde and fecha_creacion_hasta:
            return crud.obtener_usuarios_por_rango_creacion(
                fecha_inicio=fecha_creacion_desde,
                fecha_fin=fecha_creacion_hasta,
                skip=skip,
                limit=limit,
            )

        if fecha_edicion_desde and fecha_edicion_hasta:
            return crud.obtener_usuarios_por_rango_edicion(
                fecha_inicio=fecha_edicion_desde,
                fecha_fin=fecha_edicion_hasta,
                skip=skip,
                limit=limit,
            )

        if bloqueado:
            return crud.obtener_usuarios_bloqueados(skip=skip, limit=limit)

        if verificado is not None:
            return crud.obtener_usuarios_por_verificado(
                is_verified=verificado, skip=skip, limit=limit
            )

        if activo is not None:
            return crud.obtener_usuarios_por_activo(
                is_active=activo, skip=skip, limit=limit
            )

        if rol:
            return crud.obtener_usuarios_por_rol(rol=rol, skip=skip, limit=limit)

        if tipo_vinculacion:
            return crud.obtener_usuarios_por_tipo_vinculacion(
                tipo_vinculacion=tipo_vinculacion, skip=skip, limit=limit
            )

        if sede_id:
            return crud.obtener_usuarios_por_sede(
                sede_id=sede_id, skip=skip, limit=limit
            )

        if nombre:
            return crud.obtener_usuarios_por_nombre(
                nombre=nombre, skip=skip, limit=limit
            )

        return crud.obtener_usuarios(skip=skip, limit=limit)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener los usuarios: {str(e)}",
        )


@router.get("/correo/{correo}", response_model=Optional[UsuarioResponse])
async def obtener_usuario_por_correo(
    correo: str,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    crud = UsuarioCRUD(db)
    usuario = crud.obtener_usuario_por_correo(correo)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un usuario con ese correo",
        )

    return usuario


@router.get("/cedula/{cedula}", response_model=Optional[UsuarioResponse])
async def obtener_usuario_por_cedula(
    cedula: str,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    crud = UsuarioCRUD(db)
    usuario = crud.obtener_usuario_por_cedula(cedula)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un usuario con esa cédula",
        )

    return usuario


@router.get("/carnet/{carnet}", response_model=Optional[UsuarioResponse])
async def obtener_usuario_por_carnet(
    carnet: str,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    crud = UsuarioCRUD(db)
    usuario = crud.obtener_usuario_por_carnet(carnet)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un usuario con ese carné",
        )

    return usuario


@router.get("/administradores/sede/{sede_id}", response_model=List[UsuarioResponse])
async def obtener_administradores_por_sede(
    sede_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    crud = UsuarioCRUD(db)
    return crud.obtener_administradores_por_sede(
        sede_id=sede_id, skip=skip, limit=limit
    )


# ---------------------------------------------------------------------------
# Rutas con {usuario_id} — siempre al final.
# ---------------------------------------------------------------------------


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obtener_usuario(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    crud = UsuarioCRUD(db)
    usuario = crud.obtener_usuario_por_id(usuario_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return usuario


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def editar_usuario(
    usuario_id: UUID,
    data: UsuarioAdminEdit,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Corrección administrativa de datos de identificación de un usuario
    (nombre_completo, tipo_vinculacion, celular, carnet). No modera acceso
    a la cuenta; para eso usar PUT /{usuario_id}/moderacion.
    """
    try:
        crud = UsuarioCRUD(db)

        usuario = crud.obtener_usuario_por_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )

        campos_actualizacion = {
            k: v for k, v in data.model_dump().items() if v is not None
        }

        if not campos_actualizacion:
            return usuario

        return crud.actualizar_usuario(
            usuario_id=usuario_id,
            usuario_edita_id=current_admin.id_usuario,
            **campos_actualizacion,
        )

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al editar el usuario: {str(e)}",
        )


@router.put("/{usuario_id}/moderacion", response_model=UsuarioResponse)
async def moderar_usuario(
    usuario_id: UUID,
    data: UsuarioAdminUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Acciones administrativas sobre otro usuario: bloquear/desbloquear
    (is_blocked + motivo_bloqueo) y/o asignar la sede que administrará
    (sede_id, solo válido si el usuario objetivo tiene rol ADMIN).
    """
    try:
        crud = UsuarioCRUD(db)

        usuario = crud.obtener_usuario_por_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )

        if data.is_blocked is True:
            if not data.motivo_bloqueo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El motivo de bloqueo es obligatorio",
                )
            crud.bloquear_usuario(
                usuario_id=usuario_id,
                motivo_bloqueo=data.motivo_bloqueo,
                usuario_edita_id=current_admin.id_usuario,
            )
        elif data.is_blocked is False:
            crud.desbloquear_usuario(
                usuario_id=usuario_id, usuario_edita_id=current_admin.id_usuario
            )

        if data.sede_id is not None:
            crud.asignar_sede_admin(
                usuario_id=usuario_id,
                sede_id=data.sede_id,
                usuario_edita_id=current_admin.id_usuario,
            )

        return crud.obtener_usuario_por_id(usuario_id)

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al moderar el usuario: {str(e)}",
        )


@router.delete("/{usuario_id}", response_model=RespuestaAPI)
async def desactivar_usuario(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """Desactivación lógica (is_active=False); no borra el historial."""
    try:
        crud = UsuarioCRUD(db)

        usuario = crud.obtener_usuario_por_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )

        crud.desactivar_usuario(
            usuario_id=usuario_id, usuario_edita_id=current_admin.id_usuario
        )

        return RespuestaAPI(mensaje="Usuario desactivado exitosamente", exito=True)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al desactivar el usuario: {str(e)}",
        )


@router.post("/{usuario_id}/reactivar", response_model=UsuarioResponse)
async def reactivar_usuario(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    try:
        crud = UsuarioCRUD(db)

        usuario = crud.obtener_usuario_por_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )

        return crud.reactivar_usuario(
            usuario_id=usuario_id, usuario_edita_id=current_admin.id_usuario
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reactivar el usuario: {str(e)}",
        )
