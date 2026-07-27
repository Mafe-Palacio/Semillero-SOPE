from typing import List
from uuid import UUID
import traceback

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from src.core.auth import get_current_user
from src.crud.PosibleCoincidencia_crud import PosibleCoincidenciaCRUD
from src.database.config import get_db
from src.schemas.PosibleCoincidenciaSchema import (
    PosibleCoincidenciaCreate,
    PosibleCoincidenciaResponse,
    PosibleCoincidenciaUpdate,
)
from src.utils.notifications import dispatcher

router = APIRouter(
    prefix="/posibles-coincidencias",
    tags=["Posibles Coincidencias"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "", response_model=PosibleCoincidenciaResponse, status_code=status.HTTP_201_CREATED
)
async def crear_coincidencia(
    match_data: PosibleCoincidenciaCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        crud = PosibleCoincidenciaCRUD(db)
        coincidencia = crud.crear_coincidencia(
            objetoEnCustodia_id=match_data.objetoEnCustodia_id,
            reportePerdida_id=match_data.reportePerdida_id,
            usuario_id=match_data.usuario_id,
            score=match_data.score,
            notificado=True,
        )
        # Notificación asíncrona usando dispatcher
        background_tasks.add_task(
            dispatcher.notificar_match, str(match_data.usuario_id)
        )
        return coincidencia
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{coincidencia_id}", response_model=PosibleCoincidenciaResponse)
async def obtener_coincidencia(
    coincidencia_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        crud = PosibleCoincidenciaCRUD(db)
        return crud.obtener_coincidencia_de_sede_o_404(
            coincidencia_id, current_user.sede_id
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put("/{coincidencia_id}", response_model=PosibleCoincidenciaResponse)
async def actualizar_coincidencia(
    coincidencia_id: UUID,
    match_data: PosibleCoincidenciaUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        crud = PosibleCoincidenciaCRUD(db)
        # Verificamos sede antes de actualizar
        crud.obtener_coincidencia_de_sede_o_404(coincidencia_id, current_user.sede_id)

        campos = {k: v for k, v in match_data.model_dump().items() if v is not None}
        return crud.actualizar_coincidencia(
            posibleCoincidencia_id=coincidencia_id, **campos
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
