from typing import List
from uuid import UUID
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user
from src.crud.Reclamos_crud import ReclamoCRUD
from src.database.config import get_db
from src.schemas.ReclamosSchema import (
    ReclamoCreate,
    ReclamoResponse,
    ReclamoUpdate,
)
from src.schemas.schemas import RespuestaAPI

router = APIRouter(
    prefix="/reclamos",
    tags=["Reclamos"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=ReclamoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_reclamo(
    reclamo_data: ReclamoCreate,
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user) # Si necesitas sacar el usuario del token
):
    """Endpoint para enviar un nuevo reclamo."""
    try:
        crud = ReclamoCRUD(db)

        reclamo = crud.crear_reclamo(
            objetoEnCustodia_id=reclamo_data.objetoEnCustodia_id,
            usuario_id=reclamo_data.usuario_id,  # O current_user.id_usuario según tu lógica
            es_presencial=reclamo_data.es_presencial,
            evidencia_url=reclamo_data.evidencia_url,
        )
        return reclamo
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el reclamo: {str(e)}",
        )


@router.get("/{reclamo_id}", response_model=ReclamoResponse)
async def obtener_reclamo(
    reclamo_id: UUID,
    db: Session = Depends(get_db),
):
    """Endpoint para obtener el detalle de un reclamo específico."""
    try:
        crud = ReclamoCRUD(db)
        reclamo = crud.obtener_reclamo_por_id(reclamo_id)

        if not reclamo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reclamo no encontrado",
            )
        return reclamo
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el reclamo: {str(e)}",
        )


@router.put("/{reclamo_id}", response_model=ReclamoResponse)
async def actualizar_reclamo(
    reclamo_id: UUID,
    reclamo_data: ReclamoUpdate,
    db: Session = Depends(get_db),
):
    """Endpoint para actualizar el estado, cita o revisión de un reclamo."""
    try:
        crud = ReclamoCRUD(db)

        campos_actualizacion = {
            k: v for k, v in reclamo_data.model_dump().items() if v is not None
        }

        reclamo_actualizado = crud.actualizar_reclamo(
            reclamo_id=reclamo_id, **campos_actualizacion
        )

        if not reclamo_actualizado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reclamo no encontrado para actualizar",
            )

        return reclamo_actualizado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el reclamo: {str(e)}",
        )


@router.delete("/{reclamo_id}", response_model=RespuestaAPI)
async def eliminar_reclamo(
    reclamo_id: UUID,
    db: Session = Depends(get_db),
):
    """Endpoint para eliminar un reclamo."""
    try:
        crud = ReclamoCRUD(db)
        eliminado = crud.eliminar_reclamo(reclamo_id)

        if eliminado:
            return RespuestaAPI(
                mensaje="Reclamo eliminado exitosamente",
                exito=True,
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reclamo no encontrado",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el reclamo: {str(e)}",
        )
