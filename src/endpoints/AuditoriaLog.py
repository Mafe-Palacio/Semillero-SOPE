import math
from datetime import date
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_admin
from src.crud.AuditoriaLog_crud import TAMANO_PAGINA_AUDITORIA, AuditLogCRUD
from src.entities.Enums import AccionAuditoria
from src.database.config import get_db
from src.schemas.AuditoriaLogSchema import AuditLogResponse

router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoría de Sistema"],
    dependencies=[Depends(get_current_admin)],
)

# SE HAN ELIMINADO INTENCIONALMENTE LOS MÉTODOS POST, PUT Y DELETE.
# Los logs solo se leen a través de este endpoint,
# la creación (POST) se llama internamente a nivel de código desde otros CRUDs.


@router.get("", response_model=List[AuditLogResponse])
async def obtener_historial_logs(
    response: Response,
    pagina: int = Query(1, ge=1, description="Número de página (10 registros por página)"),
    entidad: Optional[str] = Query(None, description="Filtra por tipo de entidad"),
    accion: Optional[AccionAuditoria] = Query(None, description="Filtra por acción"),
    fecha_desde: Optional[date] = Query(None, description="Fecha inicial (inclusive)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha final (inclusive)"),
    db: Session = Depends(get_db),
):
    """Historial de auditoría paginado de 10 en 10 (HU10, CU21). El total viene en
    las cabeceras X-Total-Count, X-Total-Paginas, X-Pagina y X-Tamano-Pagina."""
    try:
        registros, total = AuditLogCRUD(db).obtener_logs_paginados(
            pagina=pagina,
            entidad=entidad,
            accion=accion,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )
        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Total-Paginas"] = str(
            math.ceil(total / TAMANO_PAGINA_AUDITORIA)
        )
        response.headers["X-Pagina"] = str(pagina)
        response.headers["X-Tamano-Pagina"] = str(TAMANO_PAGINA_AUDITORIA)
        return registros
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
