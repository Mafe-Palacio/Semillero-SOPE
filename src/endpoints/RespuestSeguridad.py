from typing import List
from uuid import UUID
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user
from src.crud.RespuestaSeguridad_crud import RespuestaSeguridadCRUD
from src.database.config import get_db
from src.schemas.RespuestaSeguridadSchema import (
    RespuestaSeguridadCreate,
    RespuestaSeguridadResponse,
    RespuestaSeguridadUpdate,
)
from src.schemas.schemas import RespuestaAPI

router = APIRouter(
    prefix="/respuestas-seguridad",
    tags=["Respuestas de Seguridad"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=RespuestaSeguridadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_respuesta(
    respuesta_data: RespuestaSeguridadCreate,
    db: Session = Depends(get_db),
):
    """Crea una nueva respuesta a una pregunta de seguridad."""
    try:
        crud = RespuestaSeguridadCRUD(db)

        respuesta = crud.crear_respuesta(
            reclamo_id=respuesta_data.reclamo_id,
            preguntaSeguridad_id=respuesta_data.preguntaSeguridad_id,
            respuesta_usuario=respuesta_data.respuesta_usuario,
        )
        return respuesta
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la respuesta: {str(e)}",
        )


@router.get("/reclamo/{reclamo_id}", response_model=List[RespuestaSeguridadResponse])
async def obtener_respuestas_por_reclamo(
    reclamo_id: UUID,
    db: Session = Depends(get_db),
):
    """Obtiene todas las respuestas dadas para un reclamo específico."""
    try:
        crud = RespuestaSeguridadCRUD(db)
        return crud.obtener_respuestas_por_reclamo(reclamo_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las respuestas: {str(e)}",
        )


@router.get("/{respuesta_id}", response_model=RespuestaSeguridadResponse)
async def obtener_respuesta(
    respuesta_id: UUID,
    db: Session = Depends(get_db),
):
    """Obtiene el detalle de una respuesta específica."""
    try:
        crud = RespuestaSeguridadCRUD(db)
        respuesta = crud.obtener_respuesta_por_id(respuesta_id)

        if not respuesta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Respuesta no encontrada",
            )
        return respuesta
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la respuesta: {str(e)}",
        )


@router.put("/{respuesta_id}", response_model=RespuestaSeguridadResponse)
async def actualizar_respuesta(
    respuesta_id: UUID,
    respuesta_data: RespuestaSeguridadUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza el texto de una respuesta específica."""
    try:
        crud = RespuestaSeguridadCRUD(db)

        if respuesta_data.respuesta_usuario is None:
            # Si no envían nada a actualizar, devolvemos un 400
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se enviaron datos para actualizar",
            )

        respuesta_actualizada = crud.actualizar_respuesta(
            respuestaSeguridad_id=respuesta_id,
            respuesta_usuario=respuesta_data.respuesta_usuario,
        )

        if not respuesta_actualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Respuesta no encontrada para actualizar",
            )

        return respuesta_actualizada
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la respuesta: {str(e)}",
        )


@router.delete("/{respuesta_id}", response_model=RespuestaAPI)
async def eliminar_respuesta(
    respuesta_id: UUID,
    db: Session = Depends(get_db),
):
    """Elimina una respuesta del sistema."""
    try:
        crud = RespuestaSeguridadCRUD(db)
        eliminado = crud.eliminar_respuesta(respuesta_id)

        if eliminado:
            return RespuestaAPI(
                mensaje="Respuesta eliminada exitosamente",
                exito=True,
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Respuesta no encontrada",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la respuesta: {str(e)}",
        )
