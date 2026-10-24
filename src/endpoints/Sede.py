"""
Endpoint de Sedes
"""

import traceback
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user, get_current_superadmin
from src.crud.Sede_crud import SedeCRUD
from src.database.config import get_db
from src.schemas.SedeSchema import SedeCreate, SedeResponse, SedeUpdate
from src.schemas.schemas import RespuestaAPI

router = APIRouter(
    prefix="/sedes",
    tags=["Sedes"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/", response_model=SedeResponse, status_code=status.HTTP_201_CREATED)
async def crear_sede(
    sede_data: SedeCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_superadmin),
):
    """Solo SUPERADMIN: sedes es la entidad de más alto nivel del sistema."""
    try:
        crud = SedeCRUD(db)
        return crud.crear_sede(
            nombre=sede_data.nombre,
            codigo=sede_data.codigo,
            activa=sede_data.activa,
            usuario_crea_id=current_admin.id_usuario,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la sede: {str(e)}",
        )


@router.get("/", response_model=List[SedeResponse])
async def obtener_todas_sedes(
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
    Listado de sedes. Sin parámetros, retorna todas.
    Los filtros son excluyentes entre sí y se evalúan en este orden:
    rango de creación > rango de edición > nombre > activa.
    """
    try:
        crud = SedeCRUD(db)

        if fecha_creacion_desde and fecha_creacion_hasta:
            return crud.obtener_sedes_por_rango_creacion(
                fecha_inicio=fecha_creacion_desde,
                fecha_fin=fecha_creacion_hasta,
                skip=skip,
                limit=limit,
            )

        if fecha_edicion_desde and fecha_edicion_hasta:
            return crud.obtener_sedes_por_rango_edicion(
                fecha_inicio=fecha_edicion_desde,
                fecha_fin=fecha_edicion_hasta,
                skip=skip,
                limit=limit,
            )

        if nombre:
            return crud.obtener_sedes_por_nombre(nombre=nombre, skip=skip, limit=limit)

        if activa is not None:
            return crud.obtener_sedes_por_activa(activa=activa, skip=skip, limit=limit)

        return crud.obtener_sedes(skip=skip, limit=limit)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las sedes: {str(e)}",
        )


@router.get("/codigo/{codigo}", response_model=Optional[SedeResponse])
async def obtener_sede_por_codigo(
    codigo: str,
    db: Session = Depends(get_db),
):
    try:
        crud = SedeCRUD(db)
        sede = crud.obtener_sede_por_codigo(codigo)

        if not sede:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existe una sede con ese código",
            )

        return sede

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la sede por código: {str(e)}",
        )


@router.get("/{sede_id}", response_model=SedeResponse)
async def obtener_sede(
    sede_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        crud = SedeCRUD(db)
        sede = crud.obtener_sede_por_id(sede_id)

        if not sede:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sede no encontrada",
            )

        return sede

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la sede: {str(e)}",
        )


@router.put("/{sede_id}", response_model=SedeResponse)
async def actualizar_sede(
    sede_id: UUID,
    sede_data: SedeUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_superadmin),
):
    """Solo SUPERADMIN."""
    try:
        crud = SedeCRUD(db)

        sede_existente = crud.obtener_sede_por_id(sede_id)
        if not sede_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sede no encontrada",
            )

        campos_actualizacion = {
            k: v for k, v in sede_data.dict().items() if v is not None
        }

        if not campos_actualizacion:
            return sede_existente

        return crud.actualizar_sede(
            sede_id=sede_id,
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
            detail=f"Error al actualizar la sede: {str(e)}",
        )


@router.delete("/{sede_id}", response_model=RespuestaAPI)
async def desactivar_sede(
    sede_id: UUID,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_superadmin),
):
    """Desactivación lógica (activa=False); no borra el registro (HU-Sede). Solo SUPERADMIN."""
    try:
        crud = SedeCRUD(db)

        sede = crud.obtener_sede_por_id(sede_id)
        if not sede:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sede no encontrada",
            )

        crud.desactivar_sede(sede_id=sede_id, usuario_edita_id=current_admin.id_usuario)

        return RespuestaAPI(mensaje="Sede desactivada exitosamente", exito=True)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al desactivar la sede: {str(e)}",
        )
