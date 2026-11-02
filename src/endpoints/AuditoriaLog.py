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
from src.schemas.AuditoriaLogSchema import AuditLogDetalleResponse, AuditLogResponse
from src.utils.auditoria_resumen import MODULOS, enriquecer_logs

router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoría de Sistema"],
    dependencies=[Depends(get_current_admin)],
)

# SE HAN ELIMINADO INTENCIONALMENTE LOS MÉTODOS POST, PUT Y DELETE.
# Los logs solo se leen a través de este endpoint,
# la creación (POST) se llama internamente a nivel de código desde otros CRUDs.


@router.get("", response_model=List[AuditLogDetalleResponse])
async def obtener_historial_logs(
    response: Response,
    pagina: int = Query(1, ge=1, description="Número de página (10 registros por página)"),
    entidad: Optional[str] = Query(None, description="Filtra por tipo de entidad"),
    accion: Optional[AccionAuditoria] = Query(None, description="Filtra por acción"),
    fecha_desde: Optional[date] = Query(None, description="Fecha inicial (inclusive)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha final (inclusive)"),
    modulo: Optional[str] = Query(
        None,
        description="Módulo del sitio admin: Objetos perdidos, Objetos encontrados, "
        "Objetos en custodia, Reclamos, Actas de entrega, Usuarios",
    ),
    usuario_id: Optional[UUID] = Query(None, description="Quién realizó la acción"),
    rol_actor: Optional[str] = Query(
        None, pattern="^(ADMIN|SUPERADMIN|USER)$", description="Rol de quien actuó"
    ),
    db: Session = Depends(get_db),
):
    """Historial de auditoría paginado de 10 en 10 (HU10, CU21). El total viene en
    las cabeceras X-Total-Count, X-Total-Paginas, X-Pagina y X-Tamano-Pagina.

    Cada registro trae además quién lo hizo, el módulo y un `resumen` legible
    (ej. "El administrador Ana aprobó el reporte de pérdida «Mochila» del usuario Juan").
    Para ver lo que pasa "en tiempo real" el front consulta la página 1 cada pocos
    segundos."""
    try:
        if modulo and modulo not in MODULOS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Módulo desconocido. Usa uno de: {', '.join(MODULOS)}",
            )
        registros, total = AuditLogCRUD(db).obtener_logs_paginados(
            pagina=pagina,
            entidad=entidad,
            accion=accion,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            entidades=MODULOS.get(modulo) if modulo else None,
            usuario_id=usuario_id,
            rol_actor=rol_actor,
        )
        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Total-Paginas"] = str(
            math.ceil(total / TAMANO_PAGINA_AUDITORIA)
        )
        response.headers["X-Pagina"] = str(pagina)
        response.headers["X-Tamano-Pagina"] = str(TAMANO_PAGINA_AUDITORIA)
        return enriquecer_logs(db, registros)
    except HTTPException:
        raise
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
