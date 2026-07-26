from typing import List
from uuid import UUID
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user
from src.crud.ActaEntrega_crud import ActaEntregaCRUD
from src.database.config import get_db
from src.schemas.ActaEntregaSchema import ActaEntregaCreate, ActaEntregaResponse

router = APIRouter(
    prefix="/actas-entrega",
    tags=["Actas de Entrega"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=ActaEntregaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def registrar_acta_entrega(
    acta_data: ActaEntregaCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),  # Obtenemos al admin que procesa la entrega
):
    """Crea una nueva acta de entrega para finalizar el proceso de un reclamo."""
    try:
        crud = ActaEntregaCRUD(db)

        acta = crud.crear_acta(
            reclamo_id=acta_data.reclamo_id,
            nombre_reclamante=acta_data.nombre_reclamante,
            cedula_reclamante=acta_data.cedula_reclamante,
            correo_reclamante=acta_data.correo_reclamante,
            celular_reclamante=acta_data.celular_reclamante,
            carnet_reclamante=acta_data.carnet_reclamante,
            firma_url=acta_data.firma_url,
            validacion_verbal=acta_data.validacion_verbal,
            procesada_por_admin_id=current_user.id_usuario,  # Se asigna automáticamente
        )
        return acta

    except ValueError as ve:
        # Esto atrapará el error de IntegrityError si ya existe un acta para el reclamo
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar el acta de entrega: {str(e)}",
        )


@router.get("/{acta_id}", response_model=ActaEntregaResponse)
async def obtener_acta(
    acta_id: UUID,
    db: Session = Depends(get_db),
):
    """Consulta el detalle de un acta de entrega por su ID."""
    try:
        crud = ActaEntregaCRUD(db)
        acta = crud.obtener_acta_por_id(acta_id)

        if not acta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Acta de entrega no encontrada",
            )
        return acta
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el acta: {str(e)}",
        )


@router.get("/reclamo/{reclamo_id}", response_model=ActaEntregaResponse)
async def obtener_acta_por_reclamo(
    reclamo_id: UUID,
    db: Session = Depends(get_db),
):
    """Consulta el acta de entrega asociada a un reclamo específico."""
    try:
        crud = ActaEntregaCRUD(db)
        acta = crud.obtener_acta_por_reclamo(reclamo_id)

        if not acta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existe un acta de entrega para este reclamo",
            )
        return acta
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el acta: {str(e)}",
        )
