"""
Endpoint de ObjetoEnCustodia
"""

import traceback
from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.auth import (
    get_current_admin_con_sede,
    get_current_user,
)
from src.crud.ObjetoEnCustodia_crud import ObjetoEnCustodiaCRUD
from src.crud.PublicacionEncontrado_crud import PublicacionEncontradoCRUD
from src.crud.PuntoEntrega_crud import PuntoEntregaCRUD
from src.crud.Usuario_crud import UsuarioCRUD
from src.database.config import get_db
from src.schemas.ObjetoEnCustodiaSchema import (
    ObjetoEnCustodiaCreate,
    ObjetoEnCustodiaPublico,
    ObjetoEnCustodiaResponse,
    ObjetoEnCustodiaUpdate,
)
from src.schemas.schemas import RespuestaAPI
from src.utils.notifications import NotificationDispatcher

router = APIRouter(
    prefix="/objetos-custodia",
    tags=["Objetos en Custodia"],
    dependencies=[Depends(get_current_user)],
)


def _validar_punto_entrega_de_sede(
    db: Session, puntoEntrega_id: UUID, sede_id: UUID
) -> None:
    """Verifica que un punto de entrega pertenezca a la sede del admin
    autenticado antes de dejarlo registrar/mover un objeto ahí."""
    punto = PuntoEntregaCRUD(db).obtener_punto_entrega_por_id(puntoEntrega_id)
    if not punto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El punto de entrega indicado no existe",
        )
    if punto.sede_id != sede_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El punto de entrega no pertenece a tu sede",
        )


def _obtener_objeto_de_sede_o_404(
    db: Session, objetoEnCustodia_id: UUID, sede_id: UUID
):
    """Obtiene el objeto y valida que su punto de origen pertenezca a la
    sede del admin (ObjetoEnCustodia no guarda sede_id propio)."""
    crud = ObjetoEnCustodiaCRUD(db)
    objeto = crud.obtener_objeto_custodia_por_id(objetoEnCustodia_id)

    if not objeto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objeto en custodia no encontrado",
        )

    punto = PuntoEntregaCRUD(db).obtener_punto_entrega_por_id(objeto.lugar_origen_id)
    if not punto or punto.sede_id != sede_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso sobre objetos de otra sede",
        )

    return objeto, crud


@router.post(
    "/", response_model=ObjetoEnCustodiaResponse, status_code=status.HTTP_201_CREATED
)
async def registrar_objeto_custodia(
    data: ObjetoEnCustodiaCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Registra un objeto físico ingresado a la oficina (HU03). El punto de
    entrega debe pertenecer a la sede del admin autenticado."""
    try:
        _validar_punto_entrega_de_sede(db, data.lugar_origen_id, current_admin.sede_id)

        crud = ObjetoEnCustodiaCRUD(db)
        return crud.registrar_objeto_custodia(
            admin_id=current_admin.id_usuario,
            categoria=data.categoria,
            descripcion=data.descripcion,
            lugar_origen_id=data.lugar_origen_id,
            fecha_ingreso=data.fecha_ingreso,
            publicacionEncontrado_id=data.publicacionEncontrado_id,
            imagen_url=data.imagen_url,
            detalles_internos=data.detalles_internos,
        )

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar el objeto en custodia: {str(e)}",
        )


@router.get("/catalogo", response_model=List[ObjetoEnCustodiaPublico])
async def obtener_catalogo_publico(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Vista pública del catálogo (HU01): solo objetos disponibles para
    reclamo, sin detalles_internos ni datos administrativos."""
    try:
        crud = ObjetoEnCustodiaCRUD(db)
        return crud.obtener_objetos_custodia_disponibles(skip=skip, limit=limit)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el catálogo: {str(e)}",
        )


@router.get("/", response_model=List[ObjetoEnCustodiaResponse])
async def obtener_todos_objetos_custodia(
    punto_entrega: Optional[UUID] = Query(
        None, description="Filtrar por punto de entrega"
    ),
    publicacion: Optional[UUID] = Query(
        None, description="Filtrar por publicación de hallazgo de origen"
    ),
    estado: Optional[str] = Query(
        None,
        description="Filtrar por estado ('EN_CUSTODIA', 'POR_VENCER', 'SIN_DUENO_DEFINITIVO', 'RECLAMADO')",
    ),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    disponibles: Optional[bool] = Query(
        None, description="True: solo EN_CUSTODIA y sin validación activa"
    ),
    en_proceso_validacion: Optional[bool] = Query(
        None, description="Filtra por si tienen o no un reclamo en evaluación"
    ),
    ingreso_desde: Optional[datetime] = Query(
        None, description="Rango de ingreso: inicio"
    ),
    ingreso_hasta: Optional[datetime] = Query(
        None, description="Rango de ingreso: fin"
    ),
    edicion_desde: Optional[datetime] = Query(
        None, description="Rango de edición: inicio"
    ),
    edicion_hasta: Optional[datetime] = Query(
        None, description="Rango de edición: fin"
    ),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """
    Listado administrativo de objetos en custodia (incluye detalles_internos),
    SIEMPRE acotado a la sede del admin autenticado. Todos los filtros se
    combinan libremente entre sí.
    """
    try:
        crud = ObjetoEnCustodiaCRUD(db)

        if publicacion:
            objeto = crud.obtener_objeto_custodia_por_publicacion(publicacion)
            if not objeto:
                return []
            punto = PuntoEntregaCRUD(db).obtener_punto_entrega_por_id(
                objeto.lugar_origen_id
            )
            if not punto or punto.sede_id != current_admin.sede_id:
                return []
            return [objeto]

        return crud.obtener_objetos_custodia_admin(
            sede_id=current_admin.sede_id,
            punto_entrega_id=punto_entrega,
            estado=estado,
            categoria=categoria,
            disponibles=disponibles,
            en_proceso_validacion=en_proceso_validacion,
            ingreso_desde=ingreso_desde,
            ingreso_hasta=ingreso_hasta,
            edicion_desde=edicion_desde,
            edicion_hasta=edicion_hasta,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener los objetos en custodia: {str(e)}",
        )


@router.get(
    "/{objetoEnCustodia_id}",
    response_model=Union[ObjetoEnCustodiaResponse, ObjetoEnCustodiaPublico],
)
async def obtener_objeto_custodia(
    objetoEnCustodia_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Un ADMIN de la sede dueña del objeto ve el detalle completo
    (incluye detalles_internos). Cualquier otro usuario solo lo ve si
    está en estado disponible para el catálogo público (HU01), y sin
    los campos administrativos.
    """
    try:
        crud = ObjetoEnCustodiaCRUD(db)
        objeto = crud.obtener_objeto_custodia_por_id(objetoEnCustodia_id)

        if not objeto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Objeto en custodia no encontrado",
            )

        if current_user.rol == "ADMIN" and current_user.sede_id is not None:
            punto = PuntoEntregaCRUD(db).obtener_punto_entrega_por_id(
                objeto.lugar_origen_id
            )
            if punto and punto.sede_id == current_user.sede_id:
                return ObjetoEnCustodiaResponse.model_validate(objeto)

        if objeto.estado == "EN_CUSTODIA" and not objeto.en_proceso_validacion:
            return ObjetoEnCustodiaPublico.model_validate(objeto)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objeto en custodia no encontrado",
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el objeto en custodia: {str(e)}",
        )


@router.put("/{objetoEnCustodia_id}", response_model=ObjetoEnCustodiaResponse)
async def editar_objeto_custodia(
    objetoEnCustodia_id: UUID,
    data: ObjetoEnCustodiaUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    try:
        objeto_existente, crud = _obtener_objeto_de_sede_o_404(
            db, objetoEnCustodia_id, current_admin.sede_id
        )

        campos_actualizacion = {
            k: v for k, v in data.model_dump().items() if v is not None
        }

        if not campos_actualizacion:
            return objeto_existente

        return crud.editar_objeto_custodia(
            objetoEnCustodia_id=objetoEnCustodia_id,
            usuario_edita_id=current_admin.id_usuario,
            **campos_actualizacion,
        )

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al editar el objeto en custodia: {str(e)}",
        )


@router.put("/{objetoEnCustodia_id}/bloquear", response_model=ObjetoEnCustodiaResponse)
async def bloquear_objeto_para_validacion(
    objetoEnCustodia_id: UUID,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Normalmente lo dispara el flujo de Reclamos al iniciarse una
    solicitud (HU08); se deja disponible también para intervención manual."""
    try:
        _, crud = _obtener_objeto_de_sede_o_404(
            db, objetoEnCustodia_id, current_admin.sede_id
        )
        return crud.bloquear_objeto_para_validacion(objetoEnCustodia_id)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al bloquear el objeto: {str(e)}",
        )


@router.put("/{objetoEnCustodia_id}/liberar", response_model=ObjetoEnCustodiaResponse)
async def liberar_objeto_validacion(
    objetoEnCustodia_id: UUID,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    try:
        _, crud = _obtener_objeto_de_sede_o_404(
            db, objetoEnCustodia_id, current_admin.sede_id
        )
        return crud.liberar_objeto_validacion(objetoEnCustodia_id)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al liberar el objeto: {str(e)}",
        )


@router.put(
    "/{objetoEnCustodia_id}/marcar-reclamado", response_model=ObjetoEnCustodiaResponse
)
async def marcar_objeto_reclamado(
    objetoEnCustodia_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Normalmente lo dispara el cierre del Acta de Entrega; se deja
    disponible también para corrección manual administrativa."""
    try:
        objeto, crud = _obtener_objeto_de_sede_o_404(
            db, objetoEnCustodia_id, current_admin.sede_id
        )
        objeto_actualizado = crud.marcar_objeto_reclamado(objetoEnCustodia_id)

        # HU27: si el objeto vino de una publicación de un usuario (no fue
        # ingresado directo por la admin), avisarle que su aporte sirvió.
        if objeto.publicacionEncontrado_id:
            publicacion = PublicacionEncontradoCRUD(
                db
            ).obtener_publicacion_encontrada_por_id(objeto.publicacionEncontrado_id)
            if publicacion:
                encontrador = UsuarioCRUD(db).obtener_usuario_por_id(
                    publicacion.usuario_id
                )
                if encontrador:
                    dispatcher = NotificationDispatcher()
                    background_tasks.add_task(
                        dispatcher.enviar_cierre_exitoso_encontrador,
                        correo=encontrador.correo,
                        descripcion_objeto=objeto.descripcion,
                    )

        return objeto_actualizado

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al marcar el objeto como reclamado: {str(e)}",
        )


@router.put(
    "/{objetoEnCustodia_id}/archivar-sin-dueno", response_model=ObjetoEnCustodiaResponse
)
async def archivar_objeto_sin_dueno(
    objetoEnCustodia_id: UUID,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Archiva definitivamente un objeto vencido (HU09), típicamente uno de
    los 'candidatos_a_archivar' que devuelve POST /expiracion."""
    try:
        objeto_existente, crud = _obtener_objeto_de_sede_o_404(
            db, objetoEnCustodia_id, current_admin.sede_id
        )

        if objeto_existente.estado != "POR_VENCER":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden archivar objetos en estado 'POR_VENCER'",
            )

        return crud.archivar_objeto_sin_dueno(objetoEnCustodia_id)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al archivar el objeto: {str(e)}",
        )


@router.post("/expiracion", response_model=RespuestaAPI)
async def ejecutar_expiracion_y_archivado(
    db: Session = Depends(get_db),
):
    """Rutina periódica (HU09): marca 'POR_VENCER' los objetos con ~5 meses
    en custodia y reporta los candidatos a archivar (~6 meses). Pensado
    para invocarse desde un cron/scheduler, pero expuesto también como
    disparador manual para el admin."""
    try:
        crud = ObjetoEnCustodiaCRUD(db)
        resultado = crud.ejecutar_expiracion_y_archivado()

        return RespuestaAPI(
            mensaje=(
                f"{resultado['marcados_por_vencer']} objeto(s) marcados como "
                f"POR_VENCER. {len(resultado['candidatos_a_archivar'])} candidato(s) "
                f"listos para archivar definitivamente."
            ),
            exito=True,
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar la rutina de expiración: {str(e)}",
        )
