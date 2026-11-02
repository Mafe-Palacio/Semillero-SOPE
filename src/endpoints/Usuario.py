"""
Endpoint de Usuarios
"""

import traceback
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_admin, get_current_superadmin, get_current_user
from src.crud.Usuario_crud import UsuarioCRUD
from src.database.config import get_db
from src.entities.AuditoriaLog import AuditLog
from src.entities.Enums import AccionAuditoria
from src.entities.Usuario import Usuario
from src.schemas.UsuarioSchema import (
    AdminCreate,
    CambiarPasswordRequest,
    UsuarioAdminEdit,
    UsuarioAdminUpdate,
    UsuarioResponse,
    UsuarioResumen,
    UsuarioUpdate,
)
from src.schemas.schemas import RespuestaAPI
from src.utils.notifications import NotificationDispatcher
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


def _con_actividad(crud: UsuarioCRUD, usuarios: List[Usuario]) -> List[UsuarioResumen]:
    """Convierte usuarios a UsuarioResumen agregando sus conteos."""
    conteos = crud.contar_actividad([u.usuario_id for u in usuarios])
    return [
        UsuarioResumen.model_validate(
            {**UsuarioResponse.model_validate(u).model_dump(), **conteos[u.usuario_id]}
        )
        for u in usuarios
    ]


def _exigir_superadmin_si_es_admin(usuario: Usuario, current_admin) -> None:
    """Solo un SUPERADMIN puede tocar cuentas de administradores."""
    if usuario.rol in ("ADMIN", "SUPERADMIN") and current_admin.rol != "SUPERADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un SUPERADMIN puede gestionar a otro administrador",
        )


@router.get("/resumen", response_model=List[UsuarioResumen])
async def listar_usuarios_con_actividad(
    nombre: Optional[str] = Query(None, description="Filtra por nombre parcial"),
    activo: Optional[bool] = Query(None),
    bloqueado: Optional[bool] = Query(None),
    skip: int = 0,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """Módulo "Usuarios" del sitio admin: usuarios normales (rol USER) con
    cuántos objetos han reportado como perdidos, cuántos han encontrado y cuántos
    reclamos han iniciado, cada uno con su desglose por estado."""
    consulta = db.query(Usuario).filter(Usuario.rol == "USER")
    if nombre:
        consulta = consulta.filter(Usuario.nombre_completo.ilike(f"%{nombre}%"))
    if activo is not None:
        consulta = consulta.filter(Usuario.is_active == activo)
    if bloqueado is not None:
        consulta = consulta.filter(Usuario.is_blocked == bloqueado)
    usuarios = (
        consulta.order_by(Usuario.nombre_completo).offset(skip).limit(limit).all()
    )
    return _con_actividad(UsuarioCRUD(db), usuarios)


@router.get("/administradores", response_model=List[UsuarioResponse])
async def listar_administradores(
    sede_id: Optional[UUID] = Query(None, description="Solo los de esta sede"),
    activo: Optional[bool] = Query(None),
    skip: int = 0,
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_superadmin),
):
    """Módulos del SUPERADMIN: lista de administradores (con o sin sede)."""
    consulta = db.query(Usuario).filter(Usuario.rol == "ADMIN")
    if sede_id:
        consulta = consulta.filter(Usuario.sede_id == sede_id)
    if activo is not None:
        consulta = consulta.filter(Usuario.is_active == activo)
    return consulta.order_by(Usuario.nombre_completo).offset(skip).limit(limit).all()


@router.post(
    "/administradores",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_administrador(
    data: AdminCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_superadmin),
):
    """El SUPERADMIN da de alta a un administrador: la cuenta nace verificada,
    con una contraseña temporal y, opcionalmente, ya asignada a una sede."""
    try:
        if data.sede_id is not None:
            from src.entities.Sede import Sede

            if not db.query(Sede).filter(Sede.sede_id == data.sede_id).first():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="La sede no existe"
                )
        crud = UsuarioCRUD(db)
        admin = crud.crear_administrador(
            nombre_completo=data.nombre_completo,
            cedula=data.cedula,
            correo=data.correo,
            hashed_password=hash_password(data.password_temporal),
            tipo_vinculacion=data.tipo_vinculacion.value,
            celular=data.celular,
            sede_id=data.sede_id,
            creado_por=current_admin.id_usuario,
        )
        # La alta de usuarios no entra a la auditoría automática (el registro
        # público no tiene actor); aquí sí hay un SUPERADMIN, así que se deja huella.
        db.add(
            AuditLog(
                entidad="Usuario",
                entidad_id=admin.usuario_id,
                accion=AccionAuditoria.CREAR,
                usuario_id=current_admin.id_usuario,
                detalle="Administrador creado",
            )
        )
        db.commit()
        return admin
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el administrador: {str(e)}",
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


@router.get("/{usuario_id}/resumen", response_model=UsuarioResumen)
async def obtener_resumen_usuario(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """Detalle de un usuario con sus conteos de actividad (ver /usuarios/resumen)."""
    crud = UsuarioCRUD(db)
    usuario = crud.obtener_usuario_por_id(usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
    return _con_actividad(crud, [usuario])[0]


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

        _exigir_superadmin_si_es_admin(usuario, current_admin)

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
    background_tasks: BackgroundTasks,
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

        _exigir_superadmin_si_es_admin(usuario, current_admin)
        if usuario.usuario_id == current_admin.id_usuario and data.is_blocked is True:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes bloquear tu propia cuenta",
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

            # HU06: notificar al usuario que su cuenta fue bloqueada.
            dispatcher = NotificationDispatcher()
            background_tasks.add_task(
                dispatcher.enviar_notificacion_bloqueo,
                correo=usuario.correo,
                motivo=data.motivo_bloqueo,
            )

        elif data.is_blocked is False:
            crud.desbloquear_usuario(
                usuario_id=usuario_id, usuario_edita_id=current_admin.id_usuario
            )

        if data.sede_id is not None:
            if current_admin.rol != "SUPERADMIN":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "Solo un SUPERADMIN puede reasignar la sede que "
                        "administra otro usuario"
                    ),
                )
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

        _exigir_superadmin_si_es_admin(usuario, current_admin)
        if usuario_id == current_admin.id_usuario:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes desactivar tu propia cuenta",
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

        _exigir_superadmin_si_es_admin(usuario, current_admin)

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
