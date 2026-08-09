"""
Endpoint de Reportes de Pérdida
"""

import traceback
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user, get_current_admin_con_sede
from src.crud.ReportePerdida_crud import ReportePerdidaCRUD
from src.crud.Ubicacion_crud import UbicacionCRUD
from src.database.config import get_db
from src.entities.ReportePerdida import ReportePerdida
from src.schemas.ReportePerdidaSchema import (
    ReportePerdidaCreate,
    ReportePerdidaModeracion,
    ReportePerdidaResolverEliminacion,
    ReportePerdidaResponse,
    ReportePerdidaUpdate,
)

router = APIRouter(
    prefix="/reportes-perdida",
    tags=["Reportes de Pérdida"],
    dependencies=[Depends(get_current_user)],
)


def _verificar_sede_admin(reporte: ReportePerdida, current_admin, db: Session) -> None:
    """ReportePerdida no guarda sede_id propio: se resuelve vía su ubicación
    de pérdida. Lanza 403 si el admin no administra esa sede."""
    ubicacion = UbicacionCRUD(db).obtener_ubicacion_por_id(reporte.lugar_perdida_id)
    if not ubicacion or ubicacion.sede_id != current_admin.sede_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso sobre reportes de otra sede",
        )


@router.post(
    "/", response_model=ReportePerdidaResponse, status_code=status.HTTP_201_CREATED
)
async def crear_reporte_perdida(
    data: ReportePerdidaCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        crud = ReportePerdidaCRUD(db)
        return crud.crear_reporte_perdida(
            usuario_id=current_user.id_usuario,
            categoria=data.categoria.value,
            descripcion=data.descripcion,
            lugar_perdida_id=data.lugar_perdida_id,
            fecha_perdida=data.fecha_perdida,
            hora_aproximada=data.hora_aproximada,
            imagen_url=data.imagen_url,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el reporte de pérdida: {str(e)}",
        )


@router.get("/me", response_model=List[ReportePerdidaResponse])
async def obtener_mis_reportes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    crud = ReportePerdidaCRUD(db)
    return crud.obtener_reportes_perdida_por_usuario(
        usuario_id=current_user.id_usuario, skip=skip, limit=limit
    )


@router.get("/", response_model=List[ReportePerdidaResponse])
async def obtener_reportes_perdida(
    usuario_id: Optional[UUID] = Query(None),
    categoria: Optional[str] = Query(None),
    estado: Optional[str] = Query(
        None,
        description="'PENDIENTE', 'APROBADA', 'RECHAZADA', 'ELIMINACION_PENDIENTE', 'CERRADA'",
    ),
    lugar_perdida_id: Optional[UUID] = Query(None),
    eliminacion_solicitada: Optional[bool] = Query(None),
    fecha_perdida_desde: Optional[date] = Query(None),
    fecha_perdida_hasta: Optional[date] = Query(None),
    fecha_edicion_desde: Optional[datetime] = Query(None),
    fecha_edicion_hasta: Optional[datetime] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """
    Listado administrativo, siempre acotado a la sede del admin autenticado
    (vía la ubicación de pérdida). Todos los filtros se combinan entre sí.
    """
    try:
        crud = ReportePerdidaCRUD(db)
        return crud.obtener_reportes_perdida_admin(
            sede_id=current_admin.sede_id,
            usuario_id=usuario_id,
            categoria=categoria,
            estado=estado,
            lugar_perdida_id=lugar_perdida_id,
            eliminacion_solicitada=eliminacion_solicitada,
            fecha_perdida_desde=fecha_perdida_desde,
            fecha_perdida_hasta=fecha_perdida_hasta,
            fecha_edicion_desde=fecha_edicion_desde,
            fecha_edicion_hasta=fecha_edicion_hasta,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener los reportes de pérdida: {str(e)}",
        )


@router.get("/{reporte_id}", response_model=ReportePerdidaResponse)
async def obtener_reporte_perdida(
    reporte_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """El dueño del reporte o un ADMIN de su sede pueden verlo."""
    crud = ReportePerdidaCRUD(db)
    reporte = crud.obtener_reporte_perdida_por_id(reporte_id)

    if not reporte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte no encontrado",
        )

    es_dueno = reporte.usuario_id == current_user.id_usuario
    if not es_dueno:
        if current_user.rol not in ("ADMIN", "SUPERADMIN"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver este reporte",
            )
        _verificar_sede_admin(reporte, current_user, db)

    return reporte


@router.put("/{reporte_id}", response_model=ReportePerdidaResponse)
async def editar_reporte_perdida(
    reporte_id: UUID,
    data: ReportePerdidaUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Corrección administrativa de categoría/descripción/imagen (HU07)."""
    try:
        crud = ReportePerdidaCRUD(db)
        reporte = crud.obtener_reporte_perdida_por_id(reporte_id)
        if not reporte:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporte no encontrado",
            )

        _verificar_sede_admin(reporte, current_admin, db)

        campos = {k: v for k, v in data.model_dump().items() if v is not None}
        if not campos:
            return reporte

        return crud.editar_reporte_perdida(
            reporte_perdida_id=reporte_id,
            usuario_edita_id=current_admin.id_usuario,
            **campos,
        )

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al editar el reporte: {str(e)}",
        )


@router.put("/{reporte_id}/moderacion", response_model=ReportePerdidaResponse)
async def moderar_reporte_perdida(
    reporte_id: UUID,
    data: ReportePerdidaModeracion,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Aprueba o rechaza la publicación del reporte (HU02)."""
    try:
        crud = ReportePerdidaCRUD(db)
        reporte = crud.obtener_reporte_perdida_por_id(reporte_id)
        if not reporte:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporte no encontrado",
            )

        _verificar_sede_admin(reporte, current_admin, db)

        if data.estado == "APROBADA":
            return crud.aprobar_reporte_perdida(reporte_id)

        if data.estado == "RECHAZADA":
            if not data.motivo_rechazo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El motivo de rechazo es obligatorio",
                )
            return crud.rechazar_reporte_perdida(reporte_id, data.motivo_rechazo)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado de moderación inválido; use 'APROBADA' o 'RECHAZADA'",
        )

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al moderar el reporte: {str(e)}",
        )


@router.put(
    "/{reporte_id}/solicitar-eliminacion", response_model=ReportePerdidaResponse
)
async def solicitar_eliminacion_reporte(
    reporte_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Solo el dueño del reporte puede solicitar su eliminación."""
    crud = ReportePerdidaCRUD(db)
    reporte = crud.obtener_reporte_perdida_por_id(reporte_id)

    if not reporte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte no encontrado",
        )

    if reporte.usuario_id != current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el autor del reporte puede solicitar su eliminación",
        )

    return crud.solicitar_eliminacion_reporte_perdida(reporte_id)


@router.put(
    "/{reporte_id}/resolver-eliminacion",
    response_model=Optional[ReportePerdidaResponse],
)
async def resolver_eliminacion_reporte(
    reporte_id: UUID,
    data: ReportePerdidaResolverEliminacion,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Admin aprueba (borra definitivamente) o rechaza (restaura a APROBADA)
    la solicitud de eliminación hecha por el usuario."""
    try:
        crud = ReportePerdidaCRUD(db)
        reporte = crud.obtener_reporte_perdida_por_id(reporte_id)
        if not reporte:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporte no encontrado",
            )

        _verificar_sede_admin(reporte, current_admin, db)

        return crud.resolver_solicitud_eliminacion_reporte(
            reporte_perdida_id=reporte_id, aprobar=data.aprobar, motivo=data.motivo
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al resolver la solicitud de eliminación: {str(e)}",
        )
