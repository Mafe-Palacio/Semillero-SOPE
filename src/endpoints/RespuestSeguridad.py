from typing import List
from uuid import UUID
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user
from src.crud.RespuestaSeguridad_crud import RespuestaSeguridadCRUD
from src.crud.Reclamos_crud import ReclamoCRUD
from src.crud.PreguntaSeguridad_crud import PreguntaSeguridadCRUD
from src.database.config import get_db
from src.entities.Enums import EstadoReclamo
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


def _es_dueno_o_admin(reclamo, current_user) -> bool:
    return reclamo.usuario_id == current_user.id_usuario or current_user.rol in (
        "ADMIN",
        "SUPERADMIN",
    )


@router.post(
    "",
    response_model=RespuestaSeguridadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_respuesta(
    respuesta_data: RespuestaSeguridadCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Crea una nueva respuesta a una pregunta de seguridad. Solo el dueño
    del reclamo puede responder, y solo mientras el reclamo sigue abierto
    (ENVIADO/EN_REVISION) — evita que alguien más conteste por él, o que
    se agreguen respuestas después de que el admin ya decidió."""
    try:
        reclamo_crud = ReclamoCRUD(db)
        reclamo = reclamo_crud.obtener_reclamo_por_id(respuesta_data.reclamo_id)
        if not reclamo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reclamo no encontrado"
            )

        if reclamo.usuario_id != current_user.id_usuario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el dueño del reclamo puede responder sus preguntas de seguridad",
            )

        if reclamo.estado not in (EstadoReclamo.ENVIADO, EstadoReclamo.EN_REVISION):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este reclamo ya fue procesado, no admite nuevas respuestas",
            )

        pregunta = PreguntaSeguridadCRUD(db).obtener_pregunta_seguridad_por_id(
            respuesta_data.preguntaSeguridad_id
        )
        if not pregunta or pregunta.objetoEnCustodia_id != reclamo.objetoEnCustodia_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La pregunta de seguridad no pertenece al objeto de este reclamo",
            )

        crud = RespuestaSeguridadCRUD(db)
        return crud.crear_respuesta(
            reclamo_id=respuesta_data.reclamo_id,
            preguntaSeguridad_id=respuesta_data.preguntaSeguridad_id,
            respuesta_usuario=respuesta_data.respuesta_usuario,
        )
    except HTTPException:
        raise
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
    current_user=Depends(get_current_user),
):
    """Obtiene todas las respuestas dadas para un reclamo específico.
    Solo el dueño del reclamo o un admin pueden consultarlas."""
    try:
        reclamo = ReclamoCRUD(db).obtener_reclamo_por_id(reclamo_id)
        if not reclamo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reclamo no encontrado"
            )
        if not _es_dueno_o_admin(reclamo, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver estas respuestas",
            )

        crud = RespuestaSeguridadCRUD(db)
        return crud.obtener_respuestas_por_reclamo(reclamo_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las respuestas: {str(e)}",
        )


@router.get("/{respuesta_id}", response_model=RespuestaSeguridadResponse)
async def obtener_respuesta(
    respuesta_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Obtiene el detalle de una respuesta específica. Solo el dueño del
    reclamo asociado o un admin pueden consultarla."""
    try:
        crud = RespuestaSeguridadCRUD(db)
        respuesta = crud.obtener_respuesta_por_id(respuesta_id)

        if not respuesta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Respuesta no encontrada",
            )

        reclamo = ReclamoCRUD(db).obtener_reclamo_por_id(respuesta.reclamo_id)
        if not reclamo or not _es_dueno_o_admin(reclamo, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver esta respuesta",
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
    current_user=Depends(get_current_user),
):
    """Actualiza el texto de una respuesta específica. Solo el dueño del
    reclamo, y solo mientras el reclamo sigue abierto."""
    try:
        crud = RespuestaSeguridadCRUD(db)
        respuesta = crud.obtener_respuesta_por_id(respuesta_id)
        if not respuesta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Respuesta no encontrada",
            )

        reclamo = ReclamoCRUD(db).obtener_reclamo_por_id(respuesta.reclamo_id)
        if not reclamo or reclamo.usuario_id != current_user.id_usuario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el dueño del reclamo puede editar su respuesta",
            )
        if reclamo.estado not in (EstadoReclamo.ENVIADO, EstadoReclamo.EN_REVISION):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este reclamo ya fue procesado, no admite ediciones",
            )

        if respuesta_data.respuesta_usuario is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se enviaron datos para actualizar",
            )

        return crud.actualizar_respuesta(
            respuestaSeguridad_id=respuesta_id,
            respuesta_usuario=respuesta_data.respuesta_usuario,
        )
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
    current_user=Depends(get_current_user),
):
    """Elimina una respuesta del sistema. Dueño del reclamo o admin."""
    try:
        crud = RespuestaSeguridadCRUD(db)
        respuesta = crud.obtener_respuesta_por_id(respuesta_id)
        if not respuesta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Respuesta no encontrada",
            )

        reclamo = ReclamoCRUD(db).obtener_reclamo_por_id(respuesta.reclamo_id)
        if not reclamo or not _es_dueno_o_admin(reclamo, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar esta respuesta",
            )

        crud.eliminar_respuesta(respuesta_id)
        return RespuestaAPI(mensaje="Respuesta eliminada exitosamente", exito=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la respuesta: {str(e)}",
        )
