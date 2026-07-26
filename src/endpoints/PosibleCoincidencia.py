from typing import List
from uuid import UUID
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user
from src.crud.PosibleCoincidencia_crud import PosibleCoincidenciaCRUD
from src.database.config import get_db
from src.schemas.PosibleCoincidenciaSchema import (
    PosibleCoincidenciaCreate,
    PosibleCoincidenciaResponse,
    PosibleCoincidenciaUpdate,
)
from src.schemas.schemas import RespuestaAPI

router = APIRouter(
    prefix="/posibles-coincidencias",
    tags=["Posibles Coincidencias (Smart Match)"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=PosibleCoincidenciaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_coincidencia(
    match_data: PosibleCoincidenciaCreate,
    db: Session = Depends(get_db),
):
    """Registra una nueva posible coincidencia detectada por el sistema."""
    try:
        crud = PosibleCoincidenciaCRUD(db)

        coincidencia = crud.crear_coincidencia(
            objetoEnCustodia_id=match_data.objetoEnCustodia_id,
            reportePerdida_id=match_data.reportePerdida_id,
            usuario_id=match_data.usuario_id,
            score=match_data.score,
            notificado=match_data.notificado,
        )
        return coincidencia
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar la coincidencia: {str(e)}",
        )


@router.get("/usuario/{usuario_id}", response_model=List[PosibleCoincidenciaResponse])
async def obtener_coincidencias_usuario(
    usuario_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Lista las coincidencias detectadas para un usuario específico."""
    try:
        crud = PosibleCoincidenciaCRUD(db)
        return crud.obtener_coincidencias_por_usuario(
            usuario_id, skip=skip, limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las coincidencias: {str(e)}",
        )


@router.get("/{coincidencia_id}", response_model=PosibleCoincidenciaResponse)
async def obtener_coincidencia(
    coincidencia_id: UUID,
    db: Session = Depends(get_db),
):
    """Obtiene el detalle de una coincidencia puntual."""
    try:
        crud = PosibleCoincidenciaCRUD(db)
        coincidencia = crud.obtener_coincidencia_por_id(coincidencia_id)

        if not coincidencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Coincidencia no encontrada",
            )
        return coincidencia
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la coincidencia: {str(e)}",
        )


@router.put("/{coincidencia_id}", response_model=PosibleCoincidenciaResponse)
async def actualizar_coincidencia(
    coincidencia_id: UUID,
    match_data: PosibleCoincidenciaUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza una coincidencia (útil para cambiar el estado 'notificado' a True)."""
    try:
        crud = PosibleCoincidenciaCRUD(db)

        campos_actualizacion = {
            k: v for k, v in match_data.model_dump().items() if v is not None
        }

        if not campos_actualizacion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se enviaron datos para actualizar",
            )

        coincidencia_actualizada = crud.actualizar_coincidencia(
            posibleCoincidencia_id=coincidencia_id, **campos_actualizacion
        )

        if not coincidencia_actualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Coincidencia no encontrada para actualizar",
            )

        return coincidencia_actualizada
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la coincidencia: {str(e)}",
        )


@router.delete("/{coincidencia_id}", response_model=RespuestaAPI)
async def eliminar_coincidencia(
    coincidencia_id: UUID,
    db: Session = Depends(get_db),
):
    """Elimina un registro de coincidencia (por ejemplo, si el usuario la descarta)."""
    try:
        crud = PosibleCoincidenciaCRUD(db)
        eliminado = crud.eliminar_coincidencia(coincidencia_id)

        if eliminado:
            return RespuestaAPI(
                mensaje="Coincidencia eliminada exitosamente",
                exito=True,
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coincidencia no encontrada",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la coincidencia: {str(e)}",
        )
