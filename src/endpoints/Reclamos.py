from datetime import datetime
from typing import List, Optional
from uuid import UUID
import traceback

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from src.core.auth import get_current_user, get_current_admin_con_sede
from src.crud.Reclamos_crud import ReclamoCRUD
from src.crud.ObjetoEnCustodia_crud import ObjetoEnCustodiaCRUD
from src.crud.PreguntaSeguridad_crud import PreguntaSeguridadCRUD
from src.crud.RespuestaSeguridad_crud import RespuestaSeguridadCRUD
from src.crud.Usuario_crud import UsuarioCRUD
from src.database.config import get_db
from src.schemas.ReclamosSchema import ReclamoCreate, ReclamoResponse, ReclamoUpdate
from src.schemas.schemas import RespuestaAPI
from src.entities.Enums import EstadoReclamo

from src.utils.notifications import NotificationDispatcher

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
        # 1. Bloquear el objeto a nivel de negocio (HU08 - concurrencia)
        objeto_crud = ObjetoEnCustodiaCRUD(db)
        objeto_crud.bloquear_objeto_para_validacion(reclamo_data.objetoEnCustodia_id)

        # 2. Crear el reclamo
        crud = ReclamoCRUD(db)
        reclamo = crud.crear_reclamo(
            objetoEnCustodia_id=reclamo_data.objetoEnCustodia_id,
            usuario_id=current_user.id_usuario,
            es_presencial=reclamo_data.es_presencial,
            evidencia_url=reclamo_data.evidencia_url,
        )

        # 3. Mandar correo de confirmación de envío
        dispatcher = NotificationDispatcher()
        background_tasks.add_task(
            dispatcher.enviar_cambio_estado_reclamo,
            current_user.correo,
            EstadoReclamo.ENVIADO.value,
        )

        return reclamo
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("", response_model=List[ReclamoResponse])
async def obtener_todos_reclamos(
    estado: Optional[str] = Query(None, description="Filtra por estado"),
    usuario_id: Optional[UUID] = Query(None, description="Filtra por reclamante"),
    fecha_desde: Optional[datetime] = Query(None, description="Rango de envío: inicio"),
    fecha_hasta: Optional[datetime] = Query(None, description="Rango de envío: fin"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Listado administrativo de todos los reclamos (incluye los exitosos,
    estado RECLAMADO), SIEMPRE acotado a la sede del admin autenticado."""
    try:
        crud = ReclamoCRUD(db)
        return crud.obtener_reclamos_admin(
            sede_id=current_admin.sede_id,
            estado=estado,
            usuario_id=usuario_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/me", response_model=List[ReclamoResponse])
async def obtener_mis_reclamos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Historial de reclamos propios, activos e históricos, con su estado
    actual (HU14). Debe ir ANTES de GET /{reclamo_id} en el archivo, o
    FastAPI intentaría interpretar 'me' como un UUID y fallaría con 422."""
    crud = ReclamoCRUD(db)
    return crud.obtener_reclamos_por_usuario(
        usuario_id=current_user.id_usuario, skip=skip, limit=limit
    )


@router.get("/{reclamo_id}", response_model=ReclamoResponse)
async def obtener_reclamo(
    reclamo_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """El dueño del reclamo o un ADMIN de la sede del objeto pueden verlo."""
    crud = ReclamoCRUD(db)
    reclamo = crud.obtener_reclamo_por_id(reclamo_id)

    if not reclamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reclamo no encontrado"
        )

    es_dueno = reclamo.usuario_id == current_user.id_usuario
    if not es_dueno:
        if (
            current_user.rol not in ("ADMIN", "SUPERADMIN")
            or current_user.sede_id is None
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver este reclamo",
            )
        try:
            crud.obtener_reclamo_de_sede_o_404(reclamo_id, current_user.sede_id)
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(ve))

    return reclamo


@router.put("/{reclamo_id}/cancelar", response_model=ReclamoResponse)
async def cancelar_reclamo(
    reclamo_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """El usuario cancela su propio reclamo, siempre que la administradora
    aún no haya tomado una decisión (HU15)."""
    try:
        crud = ReclamoCRUD(db)
        reclamo = crud.obtener_reclamo_por_id(reclamo_id)

        if not reclamo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reclamo no encontrado"
            )

        if reclamo.usuario_id != current_user.id_usuario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes cancelar un reclamo que no es tuyo",
            )

        if reclamo.estado not in (EstadoReclamo.ENVIADO, EstadoReclamo.EN_REVISION):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este reclamo ya fue procesado y no se puede cancelar",
            )

        reclamo_actualizado = crud.actualizar_reclamo(
            reclamo_id, estado=EstadoReclamo.CANCELADO_POR_USUARIO
        )

        # Libera el objeto para que otros usuarios puedan reclamarlo de nuevo.
        ObjetoEnCustodiaCRUD(db).liberar_objeto_validacion(reclamo.objetoEnCustodia_id)

        return reclamo_actualizado

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{reclamo_id}/validar-respuestas", response_model=ReclamoResponse)
async def validar_respuestas_reclamo(
    reclamo_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Compara automáticamente las respuestas enviadas por el reclamante
    contra `preguntas_seguridad.respuesta_correcta` y aprueba o rechaza el
    reclamo según el resultado. Antes esta comparación no la hacía nadie:
    el admin tenía que revisar manualmente ambos lados."""
    try:
        crud = ReclamoCRUD(db)
        objeto_crud = ObjetoEnCustodiaCRUD(db)

        reclamo = crud.obtener_reclamo_de_sede_o_404(reclamo_id, current_admin.sede_id)

        if reclamo.estado not in (EstadoReclamo.ENVIADO, EstadoReclamo.EN_REVISION):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este reclamo ya fue procesado y no admite validación",
            )

        respuestas = RespuestaSeguridadCRUD(db).obtener_respuestas_por_reclamo(
            reclamo_id
        )
        respuestas_dict = {
            r.preguntaSeguridad_id: r.respuesta_usuario for r in respuestas
        }

        es_correcto = PreguntaSeguridadCRUD(db).validar_respuestas_seguridad(
            objetoEnCustodia_id=reclamo.objetoEnCustodia_id,
            respuestas=respuestas_dict,
        )

        nuevo_estado = (
            EstadoReclamo.APROBADO if es_correcto else EstadoReclamo.RECHAZADO
        )
        motivo_rechazo = (
            None if es_correcto else "Respuestas de seguridad incorrectas o incompletas"
        )

        reclamo_actualizado = crud.actualizar_reclamo(
            reclamo_id,
            estado=nuevo_estado,
            fecha_revision=datetime.utcnow(),
            motivo_rechazo=motivo_rechazo,
        )

        if not es_correcto:
            objeto_crud.liberar_objeto_validacion(reclamo.objetoEnCustodia_id)

        usuario = UsuarioCRUD(db).obtener_usuario_por_id(reclamo.usuario_id)
        if usuario:
            dispatcher = NotificationDispatcher()
            background_tasks.add_task(
                dispatcher.enviar_cambio_estado_reclamo,
                usuario.correo,
                nuevo_estado.value,
                motivo_rechazo,
            )

        return reclamo_actualizado

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put("/{reclamo_id}", response_model=ReclamoResponse)
async def actualizar_reclamo(
    reclamo_id: UUID,
    reclamo_data: ReclamoUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Moderación/gestión del reclamo (cambiar estado, agendar cita, etc.) —
    exclusivo de la administradora de la sede dueña del objeto."""
    try:
        crud = ReclamoCRUD(db)
        objeto_crud = ObjetoEnCustodiaCRUD(db)

        reclamo_actual = crud.obtener_reclamo_de_sede_o_404(
            reclamo_id, current_admin.sede_id
        )

        campos_actualizacion = {
            k: v for k, v in reclamo_data.model_dump().items() if v is not None
        }
        reclamo_actualizado = crud.actualizar_reclamo(
            reclamo_id, **campos_actualizacion
        )

        # Buscamos el correo del dueño del reclamo para notificarle (no el
        # del admin que hace el cambio)
        correo_reclamante = None
        if reclamo_data.estado:
            from src.crud.Usuario_crud import UsuarioCRUD

            usuario_reclamante = UsuarioCRUD(db).obtener_usuario_por_id(
                reclamo_actual.usuario_id
            )
            correo_reclamante = (
                usuario_reclamante.correo if usuario_reclamante else None
            )

        # Lógica de liberación de objetos y correos
        if reclamo_data.estado:
            dispatcher = NotificationDispatcher()

            if reclamo_data.estado in [
                EstadoReclamo.RECHAZADO,
                EstadoReclamo.CANCELADO_POR_USUARIO,
            ]:
                objeto_crud.liberar_objeto_validacion(
                    reclamo_actual.objetoEnCustodia_id
                )
                if correo_reclamante:
                    background_tasks.add_task(
                        dispatcher.enviar_cambio_estado_reclamo,
                        correo_reclamante,
                        reclamo_data.estado.value,
                        reclamo_data.motivo_rechazo,
                    )

            elif correo_reclamante:
                background_tasks.add_task(
                    dispatcher.enviar_cambio_estado_reclamo,
                    correo_reclamante,
                    reclamo_data.estado.value,
                )

        return reclamo_actualizado
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
