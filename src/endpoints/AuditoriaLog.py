from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user
from src.crud.AuditoriaLog_crud import AuditLogCRUD
from src.database.config import get_db
from src.schemas.AuditoriaLogSchema import AuditLogResponse

router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoría de Sistema"],
    dependencies=[Depends(get_current_user)],
)

# SE HAN ELIMINADO INTENCIONALMENTE LOS MÉTODOS POST, PUT Y DELETE.
# Los logs solo se leen a través de este endpoint,
# la creación (POST) se llama internamente a nivel de código desde otros CRUDs.


@router.get("", response_model=List[AuditLogResponse])
async def obtener_historial_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    try:
        crud = AuditLogCRUD(db)
        return crud.obtener_logs(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/entidad/{entidad}/id/{entidad_id}", response_model=List[AuditLogResponse])
async def obtener_historial_por_entidad(
    entidad: str,
    entidad_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        crud = AuditLogCRUD(db)
        return crud.obtener_logs_por_entidad(entidad, entidad_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
