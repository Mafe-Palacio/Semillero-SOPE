from typing import List
from uuid import UUID
import traceback

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from src.core.auth import get_current_user
from src.crud.Reclamos_crud import ReclamoCRUD
from src.crud.ObjetoEnCustodia_crud import ObjetoEnCustodiaCRUD
from src.database.config import get_db
from src.schemas.ReclamosSchema import ReclamoCreate, ReclamoResponse, ReclamoUpdate
from src.schemas.schemas import RespuestaAPI
from src.entities.Enums import EstadoReclamo

# Importamos tu módulo de notificaciones
from src.utils.notifications import dispatcher

router = APIRouter(
    prefix="/reclamos",
    tags=["Reclamos"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=ReclamoResponse, status_code=status.HTTP_201_CREATED)
async def crear_reclamo(
    reclamo_data: ReclamoCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        # 1. Bloquear el objeto a nivel de negocio
        objeto_crud = ObjetoEnCustodiaCRUD(db)
        # Asumiendo que el método existe en tu CRUD:
        objeto_crud.bloquear_objeto_para_validacion(reclamo_data.objetoEnCustodia_id)

        # 2. Crear el reclamo
        crud = ReclamoCRUD(db)
        reclamo = crud.crear_reclamo(
            objetoEnCustodia_id=reclamo_data.objetoEnCustodia_id,
            usuario_id=current_user.usuario_id,
            es_presencial=reclamo_data.es_presencial,
            evidencia_url=reclamo_data.evidencia_url,
        )

        # 3. Mandar correo de confirmación de envío (Ejemplo)
        background_tasks.add_task(
            dispatcher.notificar_reclamo_recibido, current_user.correo
        )

        return reclamo
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{reclamo_id}", response_model=ReclamoResponse)
async def obtener_reclamo(
    reclamo_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        crud = ReclamoCRUD(db)
        # Aquí internamente el CRUD puede filtrar por sede si pasas la sede del usuario
        reclamo = crud.obtener_reclamo_de_sede_o_404(reclamo_id, current_user.sede_id)
        return reclamo
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@router.put("/{reclamo_id}", response_model=ReclamoResponse)
async def actualizar_reclamo(
    reclamo_id: UUID,
    reclamo_data: ReclamoUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        crud = ReclamoCRUD(db)
        objeto_crud = ObjetoEnCustodiaCRUD(db)

        reclamo_actual = crud.obtener_reclamo_de_sede_o_404(
            reclamo_id, current_user.sede_id
        )

        campos_actualizacion = {
            k: v for k, v in reclamo_data.model_dump().items() if v is not None
        }
        reclamo_actualizado = crud.actualizar_reclamo(
            reclamo_id, **campos_actualizacion
        )

        # Lógica de liberación de objetos y correos
        if reclamo_data.estado:
            if reclamo_data.estado in [
                EstadoReclamo.RECHAZADO,
                EstadoReclamo.CANCELADO_POR_USUARIO,
            ]:
                objeto_crud.liberar_objeto_validacion(
                    reclamo_actual.objetoEnCustodia_id
                )
                background_tasks.add_task(
                    dispatcher.notificar_reclamo_rechazado, current_user.correo
                )

            elif reclamo_data.estado == EstadoReclamo.APROBADO:
                background_tasks.add_task(
                    dispatcher.notificar_reclamo_aprobado, current_user.correo
                )

        return reclamo_actualizado
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
