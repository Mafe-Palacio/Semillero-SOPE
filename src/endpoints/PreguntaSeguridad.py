"""
Endpoint de PreguntaSeguridad

Las respuestas correctas solo se exponen a ADMIN de la sede dueña del
objeto. Cualquier usuario autenticado puede ver la versión pública del
cuestionario (sin respuesta_correcta) para responderlo al reclamar (HU20).
"""

import traceback
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_admin_con_sede, get_current_user
from src.crud.ObjetoEnCustodia_crud import ObjetoEnCustodiaCRUD
from src.crud.PreguntaSeguridad_crud import PreguntaSeguridadCRUD
from src.crud.PuntoEntrega_crud import PuntoEntregaCRUD
from src.database.config import get_db
from src.schemas.PreguntaSeguridadSchema import (
    PreguntaSeguridadEdit,
    PreguntaSeguridadPublica,
    PreguntaSeguridadResponse,
    PreguntasSeguridadBulkCreate,
)
from src.schemas.schemas import RespuestaAPI

router = APIRouter(
    prefix="/preguntas-seguridad",
    tags=["Preguntas de Seguridad"],
    dependencies=[Depends(get_current_user)],
)


def _validar_objeto_de_sede(db: Session, objetoEnCustodia_id: UUID, sede_id: UUID):
    """Verifica que el objeto exista y que su punto de origen pertenezca
    a la sede del admin autenticado (ObjetoEnCustodia no guarda sede_id)."""
    objeto = ObjetoEnCustodiaCRUD(db).obtener_objeto_custodia_por_id(
        objetoEnCustodia_id
    )
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

    return objeto


def _validar_pregunta_de_sede_admin(
    db: Session, preguntaSeguridad_id: UUID, sede_id: UUID
):
    """Igual que la anterior, pero partiendo de una pregunta puntual."""
    crud = PreguntaSeguridadCRUD(db)
    pregunta = crud.obtener_pregunta_seguridad_por_id(preguntaSeguridad_id)
    if not pregunta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pregunta de seguridad no encontrada",
        )

    _validar_objeto_de_sede(db, pregunta.objetoEnCustodia_id, sede_id)

    return pregunta, crud


@router.post(
    "/objeto/{objetoEnCustodia_id}",
    response_model=List[PreguntaSeguridadResponse],
    status_code=status.HTTP_201_CREATED,
)
async def crear_preguntas_seguridad(
    objetoEnCustodia_id: UUID,
    data: PreguntasSeguridadBulkCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """La administradora define la cantidad de preguntas que considere
    apropiada para el objeto (HU04)."""
    try:
        if data.objetoEnCustodia_id != objetoEnCustodia_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El objeto indicado en la URL no coincide con el del cuerpo de la solicitud",
            )

        _validar_objeto_de_sede(db, objetoEnCustodia_id, current_admin.sede_id)

        crud = PreguntaSeguridadCRUD(db)
        preguntas_dict = [p.model_dump() for p in data.preguntas]

        return crud.crear_preguntas_seguridad(
            objetoEnCustodia_id=objetoEnCustodia_id, preguntas=preguntas_dict
        )

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear las preguntas de seguridad: {str(e)}",
        )


@router.get(
    "/objeto/{objetoEnCustodia_id}", response_model=List[PreguntaSeguridadResponse]
)
async def obtener_preguntas_seguridad_admin(
    objetoEnCustodia_id: UUID,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Vista administrativa completa, incluye respuesta_correcta."""
    try:
        _validar_objeto_de_sede(db, objetoEnCustodia_id, current_admin.sede_id)

        crud = PreguntaSeguridadCRUD(db)
        return crud.obtener_preguntas_seguridad_por_objeto(objetoEnCustodia_id)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las preguntas de seguridad: {str(e)}",
        )


@router.get(
    "/objeto/{objetoEnCustodia_id}/publico",
    response_model=List[PreguntaSeguridadPublica],
)
async def obtener_preguntas_seguridad_publicas(
    objetoEnCustodia_id: UUID,
    db: Session = Depends(get_db),
):
    """Vista sin respuesta_correcta, para que cualquier usuario autenticado
    responda el cuestionario al iniciar un reclamo (HU20)."""
    try:
        crud = PreguntaSeguridadCRUD(db)
        preguntas = crud.obtener_preguntas_seguridad_por_objeto(objetoEnCustodia_id)

        if not preguntas:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Este objeto no tiene preguntas de seguridad configuradas",
            )

        return preguntas

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el cuestionario: {str(e)}",
        )


@router.get("/{preguntaSeguridad_id}", response_model=PreguntaSeguridadResponse)
async def obtener_pregunta_seguridad(
    preguntaSeguridad_id: UUID,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    try:
        pregunta, _ = _validar_pregunta_de_sede_admin(
            db, preguntaSeguridad_id, current_admin.sede_id
        )
        return pregunta

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la pregunta de seguridad: {str(e)}",
        )


@router.put("/{preguntaSeguridad_id}", response_model=PreguntaSeguridadResponse)
async def actualizar_pregunta_seguridad(
    preguntaSeguridad_id: UUID,
    data: PreguntaSeguridadEdit,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Corrige el texto o la respuesta de una pregunta puntual. Se
    recomienda usar esto solo antes de que existan reclamos activos
    evaluándola, para no invalidar respuestas ya enviadas."""
    try:
        _, crud = _validar_pregunta_de_sede_admin(
            db, preguntaSeguridad_id, current_admin.sede_id
        )

        if data.pregunta is None and data.respuesta_correcta is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debes enviar al menos un campo para actualizar",
            )

        return crud.actualizar_pregunta_seguridad(
            preguntaSeguridad_id=preguntaSeguridad_id,
            pregunta=data.pregunta,
            respuesta_correcta=data.respuesta_correcta,
        )

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la pregunta de seguridad: {str(e)}",
        )


@router.delete("/{preguntaSeguridad_id}", response_model=RespuestaAPI)
async def eliminar_pregunta_seguridad(
    preguntaSeguridad_id: UUID,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    try:
        _, crud = _validar_pregunta_de_sede_admin(
            db, preguntaSeguridad_id, current_admin.sede_id
        )

        crud.eliminar_pregunta_seguridad(preguntaSeguridad_id)

        return RespuestaAPI(
            mensaje="Pregunta de seguridad eliminada exitosamente", exito=True
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la pregunta de seguridad: {str(e)}",
        )


@router.delete("/objeto/{objetoEnCustodia_id}", response_model=RespuestaAPI)
async def eliminar_preguntas_seguridad_de_objeto(
    objetoEnCustodia_id: UUID,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Elimina TODO el cuestionario de un objeto, ej. para reconfigurarlo desde cero."""
    try:
        _validar_objeto_de_sede(db, objetoEnCustodia_id, current_admin.sede_id)

        crud = PreguntaSeguridadCRUD(db)
        cantidad = crud.eliminar_preguntas_seguridad_de_objeto(objetoEnCustodia_id)

        return RespuestaAPI(
            mensaje=f"{cantidad} pregunta(s) de seguridad eliminadas", exito=True
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar las preguntas de seguridad: {str(e)}",
        )
