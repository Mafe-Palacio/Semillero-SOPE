from typing import List
from uuid import UUID
import traceback

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from src.core.auth import (
    get_current_user,
    get_current_admin,
    get_current_admin_con_sede,
)
from src.crud.PosibleCoincidencia_crud import PosibleCoincidenciaCRUD
from src.crud.ObjetoEnCustodia_crud import ObjetoEnCustodiaCRUD
from src.crud.ReportePerdida_crud import ReportePerdidaCRUD
from src.crud.Usuario_crud import UsuarioCRUD
from src.database.config import get_db
from src.schemas.PosibleCoincidenciaSchema import (
    PosibleCoincidenciaCreate,
    PosibleCoincidenciaResponse,
    PosibleCoincidenciaUpdate,
)
from src.schemas.schemas import RespuestaAPI
from src.utils.notifications import NotificationDispatcher

router = APIRouter(
    prefix="/posibles-coincidencias",
    tags=["Posibles Coincidencias"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/ejecutar-matching", response_model=RespuestaAPI)
async def ejecutar_matching(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """Rutina periódica de Smart Match (HU25): compara reportes de pérdida
    aprobados contra objetos en custodia disponibles (categoría + sede +
    proximidad de fecha) y registra las coincidencias que superen el
    umbral. Pensada para un scheduler, pero también disparable manualmente
    para pruebas — igual que POST /objetos-custodia/expiracion."""
    try:
        reportes = ReportePerdidaCRUD(db).obtener_reportes_perdida_elegibles_para_match(
            limit=1000
        )
        objetos = ObjetoEnCustodiaCRUD(db).obtener_objetos_custodia_disponibles(
            limit=1000
        )

        crud = PosibleCoincidenciaCRUD(db)
        nuevas = crud.generar_coincidencias_automaticas(reportes, objetos)

        usuario_crud = UsuarioCRUD(db)
        objeto_crud = ObjetoEnCustodiaCRUD(db)
        dispatcher = NotificationDispatcher()

        for coincidencia in nuevas:
            usuario = usuario_crud.obtener_usuario_por_id(coincidencia.usuario_id)
            objeto = objeto_crud.obtener_objeto_custodia_por_id(
                coincidencia.objetoEnCustodia_id
            )
            if usuario and objeto:
                background_tasks.add_task(
                    dispatcher.enviar_alerta_match,
                    usuario.correo,
                    objeto.descripcion,
                )
                crud.actualizar_coincidencia(
                    coincidencia.posibleCoincidencia_id, notificado=True
                )

        return RespuestaAPI(
            mensaje=f"{len(nuevas)} coincidencia(s) nueva(s) detectada(s) y notificada(s).",
            exito=True,
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar el matching: {str(e)}",
        )


@router.post(
    "", response_model=PosibleCoincidenciaResponse, status_code=status.HTTP_201_CREATED
)
async def crear_coincidencia(
    match_data: PosibleCoincidenciaCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Registra una posible coincidencia manualmente. Ahora restringido a
    ADMIN/SUPERADMIN: antes cualquier usuario logueado podía llamar este
    POST directamente y crear una coincidencia falsa entre cualquier
    objeto y cualquier reporte, disparando una notificación a otro
    usuario. El algoritmo automático (POST /ejecutar-matching) sigue
    siendo el flujo normal; esto queda para corrección manual de un admin.
    """
    try:
        crud = PosibleCoincidenciaCRUD(db)
        coincidencia = crud.crear_coincidencia(
            objetoEnCustodia_id=match_data.objetoEnCustodia_id,
            reportePerdida_id=match_data.reportePerdida_id,
            usuario_id=match_data.usuario_id,
            score=match_data.score,
            notificado=True,
        )

        # Buscamos el correo real del usuario y la descripción del objeto
        # para armar la notificación (antes se mandaba el UUID crudo).
        usuario = UsuarioCRUD(db).obtener_usuario_por_id(match_data.usuario_id)
        objeto = ObjetoEnCustodiaCRUD(db).obtener_objeto_custodia_por_id(
            match_data.objetoEnCustodia_id
        )

        if usuario and objeto:
            dispatcher = NotificationDispatcher()
            background_tasks.add_task(
                dispatcher.enviar_alerta_match,
                usuario.correo,
                objeto.descripcion,
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
    current_admin=Depends(get_current_admin_con_sede),
):
    """Solo ADMIN de la sede dueña del objeto — implica datos de otro usuario."""
    try:
        crud = PosibleCoincidenciaCRUD(db)
        return crud.obtener_coincidencia_de_sede_o_404(
            coincidencia_id, current_admin.sede_id
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
    current_admin=Depends(get_current_admin_con_sede),
):
    try:
        crud = PosibleCoincidenciaCRUD(db)
        crud.obtener_coincidencia_de_sede_o_404(coincidencia_id, current_admin.sede_id)

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
