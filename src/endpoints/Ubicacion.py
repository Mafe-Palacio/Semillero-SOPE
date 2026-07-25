"""
Endpoint de Ubicaciones
"""

import traceback
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user, get_current_admin_con_sede
from src.crud.Ubicacion_crud import UbicacionCRUD
from src.database.config import get_db
from src.schemas.UbicacionSchema import (
    UbicacionCreate,
    UbicacionResponse,
    UbicacionUpdate,
)
from src.schemas.schemas import RespuestaAPI

router = APIRouter(
    prefix="/ubicaciones",
    tags=["Ubicaciones"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/", response_model=UbicacionResponse, status_code=status.HTTP_201_CREATED)
async def crear_ubicacion(
    ubicacion_data: UbicacionCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Solo un ADMIN puede crear ubicaciones, y únicamente dentro de SU
    propia sede — se ignora cualquier sede_id que venga en el body."""
    try:
        crud = UbicacionCRUD(db)
        return crud.crear_ubicacion(
            sede_id=current_admin.sede_id, 
            nombre=ubicacion_data.nombre,
            tipo=ubicacion_data.tipo,
            activa=ubicacion_data.activa,
            usuario_crea_id=current_admin.id_usuario,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la ubicacion: {str(e)}",
        )


@router.get("/", response_model=List[UbicacionResponse])
async def obtener_todas_ubicaciones(
    sede: Optional[UUID] = Query(None, description="Filtrar por sede"),
    tipo: Optional[str] = Query(
        None,
        description="Filtrar por tipo de ubicacion (ej. 'BLOQUE', 'PORTERIA', 'ZONA_COMUN', 'OTRO')",
    ),
    nombre: Optional[str] = Query(
        None, description="Filtra por nombre parcial (ej. 'frat')"
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
    Listado de ubicaciones. Sin parámetros, retorna todas las activas.

    A diferencia de los demás filtros (que son excluyentes entre sí),
    `tipo` y `sede` SÍ se combinan: si mandas ambos, filtra por tipo
    dentro de esa sede; si mandas solo uno, filtra por ese único criterio.

    Orden de precedencia si mandan varios filtros a la vez:
    rango de creación > rango de edición > nombre > activa > tipo/sede.
    """
    try:
        crud = UbicacionCRUD(db)

        if fecha_creacion_desde and fecha_creacion_hasta:
            return crud.obtener_ubicaciones_por_rango_creacion(
                fecha_inicio=fecha_creacion_desde,
                fecha_fin=fecha_creacion_hasta,
                skip=skip,
                limit=limit,
            )

        if fecha_edicion_desde and fecha_edicion_hasta:
            return crud.obtener_ubicaciones_por_rango_edicion(
                fecha_inicio=fecha_edicion_desde,
                fecha_fin=fecha_edicion_hasta,
                skip=skip,
                limit=limit,
            )

        if nombre:
            return crud.obtener_ubicaciones_por_nombre(
                nombre=nombre, skip=skip, limit=limit
            )

        if activa is not None:
            return crud.obtener_ubicaciones_por_activa(
                activa=activa, skip=skip, limit=limit
            )

        if tipo:
            return crud.obtener_ubicaciones_por_tipo(
                tipo=tipo, sede_id=sede, skip=skip, limit=limit
            )

        if sede:
            return crud.obtener_ubicaciones_por_sede(
                sede_id=sede, skip=skip, limit=limit
            )

        return crud.obtener_ubicaciones(skip=skip, limit=limit)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las ubicaciones: {str(e)}",
        )


@router.get("/{ubicacion_id}", response_model=UbicacionResponse)
async def obtener_ubicacion(
    ubicacion_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        crud = UbicacionCRUD(db)
        ubicacion = crud.obtener_ubicacion_por_id(ubicacion_id)

        if not ubicacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ubicacion no encontrada",
            )

        return ubicacion

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la ubicacion: {str(e)}",
        )


@router.put("/{ubicacion_id}", response_model=UbicacionResponse)
async def actualizar_ubicacion(
    ubicacion_id: UUID,
    ubicacion_data: UbicacionUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    try:
        crud = UbicacionCRUD(db)

        ubicacion_existente = crud.obtener_ubicacion_por_id(ubicacion_id)
        if not ubicacion_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ubicacion no encontrada",
            )

        if ubicacion_existente.sede_id != current_admin.sede_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso sobre ubicaciones de otra sede",
            )

        campos_actualizacion = {
            k: v for k, v in ubicacion_data.dict().items() if v is not None
        }

        if not campos_actualizacion:
            return ubicacion_existente

        return crud.actualizar_ubicacion(
            ubicacion_id=ubicacion_id,
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
            detail=f"Error al actualizar la ubicacion: {str(e)}",
        )


@router.delete("/{ubicacion_id}", response_model=RespuestaAPI)
async def eliminar_ubicacion(
    ubicacion_id: UUID,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Desactivación lógica (activa=False); no borra el registro.
    Solo permitido dentro de la sede del admin autenticado."""
    try:
        crud = UbicacionCRUD(db)

        ubicacion = crud.obtener_ubicacion_por_id(ubicacion_id)
        if not ubicacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ubicacion no encontrada",
            )

        if ubicacion.sede_id != current_admin.sede_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso sobre ubicaciones de otra sede",
            )

        crud.desactivar_ubicacion(
            ubicacion_id=ubicacion_id, usuario_edita_id=current_admin.id_usuario
        )

        return RespuestaAPI(mensaje="Ubicacion desactivada exitosamente", exito=True)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al desactivar la ubicacion: {str(e)}",
        )