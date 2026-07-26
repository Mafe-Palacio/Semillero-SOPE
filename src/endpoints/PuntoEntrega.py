"""
Endpoint de Puntos de Entrega
"""

import traceback
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user, get_current_admin_con_sede
from src.crud.PuntoEntrega_crud import PuntoEntregaCRUD
from src.database.config import get_db
from src.schemas.PuntoEntregaSchema import (
    PuntoEntregaCreate,
    PuntoEntregaResponse,
    PuntoEntregaUpdate,
)
from src.schemas.schemas import RespuestaAPI

router = APIRouter(
    prefix="/puntos-entrega",
    tags=["Puntos Entrega"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/", response_model=PuntoEntregaResponse, status_code=status.HTTP_201_CREATED
)
async def crear_punto_entrega(
    punto_entrega_data: PuntoEntregaCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    try:
        crud = PuntoEntregaCRUD(db)
        return crud.crear_punto_entrega(
            sede_id=current_admin.sede_id,
            nombre=punto_entrega_data.nombre,
            tipo=punto_entrega_data.tipo,
            activa=punto_entrega_data.activa,
            usuario_crea_id=current_admin.id_usuario,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el punto de entrega: {str(e)}",
        )


@router.get("/", response_model=List[PuntoEntregaResponse])
async def obtener_todos_puntos_entrega(
    sede_id: Optional[UUID] = Query(None, description="Filtrar por sede"),
    tipo: Optional[str] = Query(
        None,
        description="Filtrar por tipo punto de entrega (ej. 'OFICINA', 'PORTERIA')",
    ),
    nombre: Optional[str] = Query(
        None, description="Filtra por nombre parcial (ej. 'ofi')"
    ),
    activa: Optional[bool] = Query(
        None, description="Filtra por estado activo/inactivo"
    ),
    fecha_creacion_desde: Optional[datetime] = Query(
        None, description="Rango de creación: inicio"
    ),
    fecha_creacion_hasta: Optional[datetime] = Query(
        None, description="Rango de creación: fin"
    ),
    fecha_edicion_desde: Optional[datetime] = Query(
        None, description="Rango de edición: inicio"
    ),
    fecha_edicion_hasta: Optional[datetime] = Query(
        None, description="Rango de edición: fin"
    ),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Listado de puntos de entrega. Sin parámetros, retorna todos los activos.

    `sede_id` se combina con cualquier otro filtro (nombre, tipo, activa,
    rangos de fecha); el resto de filtros son excluyentes entre sí.
    Orden de precedencia si mandan varios a la vez:
    rango de creación > rango de edición > nombre > activa > tipo.
    """
    try:
        crud = PuntoEntregaCRUD(db)

        if fecha_creacion_desde and fecha_creacion_hasta:
            return crud.obtener_puntos_entrega_por_rango_creacion(
                fecha_inicio=fecha_creacion_desde,
                fecha_fin=fecha_creacion_hasta,
                sede_id=sede_id,
                skip=skip,
                limit=limit,
            )

        if fecha_edicion_desde and fecha_edicion_hasta:
            return crud.obtener_puntos_entrega_por_rango_edicion(
                fecha_inicio=fecha_edicion_desde,
                fecha_fin=fecha_edicion_hasta,
                sede_id=sede_id,
                skip=skip,
                limit=limit,
            )

        if nombre:
            return crud.obtener_puntos_entrega_por_nombre(
                nombre=nombre, sede_id=sede_id, skip=skip, limit=limit
            )

        if activa is not None:
            return crud.obtener_puntos_entrega_por_activa(
                activa=activa, sede_id=sede_id, skip=skip, limit=limit
            )

        if tipo:
            return crud.obtener_puntos_entrega_por_tipo(
                tipo=tipo, sede_id=sede_id, skip=skip, limit=limit
            )

        if sede_id:
            return crud.obtener_puntos_entrega_por_sede(
                sede_id=sede_id, skip=skip, limit=limit
            )

        return crud.obtener_puntos_entregas(skip=skip, limit=limit)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener los puntos de entregas: {str(e)}",
        )


@router.get("/{puntoEntrega_id}", response_model=PuntoEntregaResponse)
async def obtener_punto_entrega(
    puntoEntrega_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        crud = PuntoEntregaCRUD(db)
        punto_entrega = crud.obtener_punto_entrega_por_id(puntoEntrega_id)

        if not punto_entrega:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Punto de entrega no encontrada",
            )

        return punto_entrega

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el punto de entrega: {str(e)}",
        )


@router.put("/{puntoEntrega_id}", response_model=PuntoEntregaResponse)
async def actualizar_punto_entrega(
    puntoEntrega_id: UUID,
    punto_entrega_data: PuntoEntregaUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    try:
        crud = PuntoEntregaCRUD(db)

        punto_entrega_existente = crud.obtener_punto_entrega_por_id(puntoEntrega_id)
        if not punto_entrega_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Punto de entrega no encontrada",
            )

        if punto_entrega_existente.sede_id != current_admin.sede_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso sobre puntos de entregas de otra sede",
            )

        campos_actualizacion = {
            k: v for k, v in punto_entrega_data.dict().items() if v is not None
        }

        if not campos_actualizacion:
            return punto_entrega_existente

        return crud.actualizar_punto_entrega(
            puntoEntrega_id=puntoEntrega_id,
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
            detail=f"Error al actualizar el punto de entrega: {str(e)}",
        )


@router.delete("/{puntoEntrega_id}", response_model=RespuestaAPI)
async def desactivar_punto_entrega(
    puntoEntrega_id: UUID,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    try:
        crud = PuntoEntregaCRUD(db)

        punto_entrega = crud.obtener_punto_entrega_por_id(puntoEntrega_id)
        if not punto_entrega:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Punto de entrega no encontrada",
            )

        if punto_entrega.sede_id != current_admin.sede_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso sobre puntos de entregas de otra sede",
            )

        crud.desactivar_punto_entrega(
            puntoEntrega_id=puntoEntrega_id, usuario_edita_id=current_admin.id_usuario
        )

        return RespuestaAPI(
            mensaje="Punto de entrega desactivada exitosamente", exito=True
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al desactivar el punto de entrega: {str(e)}",
        )
