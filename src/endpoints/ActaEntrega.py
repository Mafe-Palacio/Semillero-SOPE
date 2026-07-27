from uuid import UUID
import traceback
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from src.core.auth import get_current_user
from src.crud.ActaEntrega_crud import ActaEntregaCRUD
from src.crud.Reclamos_crud import ReclamoCRUD
from src.crud.ObjetoEnCustodia_crud import ObjetoEnCustodiaCRUD
from src.database.config import get_db
from src.schemas.ActaEntregaSchema import ActaEntregaCreate, ActaEntregaResponse
from src.utils.notifications import NotificationDispatcher

router = APIRouter(
    prefix="/actas-entrega",
    tags=["Actas de Entrega"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "", response_model=ActaEntregaResponse, status_code=status.HTTP_201_CREATED
)
async def registrar_acta_entrega(
    acta_data: ActaEntregaCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        reclamo_crud = ReclamoCRUD(db)
        reclamo = reclamo_crud.obtener_reclamo_de_sede_o_404(
            acta_data.reclamo_id, current_user.sede_id
        )

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
            procesada_por_admin_id=current_user.usuario_id,
        )

        objeto_crud = ObjetoEnCustodiaCRUD(db)
        objeto_crud.marcar_objeto_reclamado(reclamo.objetoEnCustodia_id)

        dispatcher = NotificationDispatcher()
        background_tasks.add_task(
            dispatcher.enviar_correo_acta_entrega,
            acta_data.correo_reclamante,
            acta_data.firma_url,
        )
        return acta
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{acta_id}", response_model=ActaEntregaResponse)
async def obtener_acta(
    acta_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    try:
        crud = ActaEntregaCRUD(db)
        return crud.obtener_acta_de_sede_o_404(acta_id, current_user.sede_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
