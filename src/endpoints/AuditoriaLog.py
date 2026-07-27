from typing import List
from uuid import UUID
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user
from src.crud.AuditoriaLog_crud import AuditLogCRUD
from src.database.config import get_db
from src.schemas.AuditoriaLogSchema import AuditLogCreate, AuditLogResponse

router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoría de Sistema"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=AuditLogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def registrar_log(
    log_data: AuditLogCreate,
    db: Session = Depends(get_db),
):
    """Endpoint para registrar un evento en la bitácora del sistema."""
    try:
        crud = AuditLogCRUD(db)

        log = crud.crear_log(
            entidad=log_data.entidad,
            entidad_id=log_data.entidad_id,
            accion=log_data.accion,
            usuario_id=log_data.usuario_id,
            detalle=log_data.detalle,
        )
        return log
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar auditoría: {str(e)}",
        )


@router.get("", response_model=List[AuditLogResponse])
async def obtener_historial_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Obtiene el listado general de eventos ordenados por fecha."""
    try:
        crud = AuditLogCRUD(db)
        return crud.obtener_logs(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener los logs: {str(e)}",
        )


@router.get("/entidad/{entidad}/id/{entidad_id}", response_model=List[AuditLogResponse])
async def obtener_historial_por_entidad(
    entidad: str,
    entidad_id: UUID,
    db: Session = Depends(get_db),
):
    """Devuelve todo el ciclo de vida o cambios que ha sufrido un registro específico."""
    try:
        crud = AuditLogCRUD(db)
        return crud.obtener_logs_por_entidad(entidad, entidad_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al buscar el historial de la entidad: {str(e)}",
        )
