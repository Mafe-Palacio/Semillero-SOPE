"""
Dashboard de métricas (HU12 / CU19) y exportación CSV/Excel (HU13 / CU20).
Ambos trabajan sobre la sede del admin (o la que el SUPERADMIN eligió con X-Sede-Id).
"""

from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.core.auth import get_current_admin_con_sede, get_current_user
from src.crud.Analitica_crud import RECURSOS_EXPORTABLES, AnaliticaCRUD
from src.database.config import get_db
from src.crud.AuditoriaLog_crud import AuditLogCRUD
from src.entities.Enums import AccionAuditoria
from src.entities.Enums import CategoriaObjeto
from src.utils.auditoria_resumen import enriquecer_logs
from src.schemas.AnaliticaSchema import MetricasResumen
from src.utils.exportacion import a_csv, a_xlsx

metricas_router = APIRouter(
    prefix="/metricas", tags=["Analítica"], dependencies=[Depends(get_current_user)]
)
exportaciones_router = APIRouter(
    prefix="/exportaciones", tags=["Analítica"], dependencies=[Depends(get_current_user)]
)

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _validar_fechas(desde: Optional[date], hasta: Optional[date]) -> None:
    if desde and hasta and desde > hasta:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fecha_desde no puede ser posterior a fecha_hasta",
        )


@metricas_router.get("/resumen", response_model=MetricasResumen)
async def resumen_metricas(
    fecha_desde: Optional[date] = Query(None, description="Inclusive"),
    fecha_hasta: Optional[date] = Query(None, description="Inclusive"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Tarjetas y gráficos del panel principal: objetos reclamados vs. sin reclamar,
    porcentaje devuelto, días promedio de custodia, categorías con más pérdidas,
    reclamos por estado y cuántas publicaciones esperan aprobación."""
    _validar_fechas(fecha_desde, fecha_hasta)
    return AnaliticaCRUD(db).metricas(current_admin.sede_id, fecha_desde, fecha_hasta)


def _datos_auditoria(db, sede_id, desde, hasta, entidad, accion):
    """Bitácora de la sede (HU10 + HU13): mismas reglas de visibilidad que GET /auditoria."""
    registros = AuditLogCRUD(db).obtener_logs_para_exportar(
        entidad=entidad,
        accion=accion,
        fecha_desde=desde,
        fecha_hasta=hasta,
        sede_id=sede_id,
    )
    columnas = ["Fecha", "Módulo", "Acción", "Entidad", "Usuario", "Rol", "Resumen"]
    filas = [
        (
            r["fecha"],
            r.get("modulo"),
            r["accion"],
            r["entidad"],
            r.get("usuario_nombre"),
            r.get("usuario_rol"),
            r.get("resumen"),
        )
        for r in enriquecer_logs(db, registros)
    ]
    return columnas, filas


@exportaciones_router.get(
    "/{recurso}",
    responses={200: {"content": {"text/csv": {}, XLSX: {}}}},
    summary="Descargar un reporte en CSV o Excel",
)
async def exportar(
    recurso: Literal[
        "entregas",
        "objetos-custodia",
        "reportes-perdida",
        "publicaciones-encontradas",
        "auditoria",
    ],
    formato: Literal["csv", "xlsx"] = Query("xlsx"),
    fecha_desde: Optional[date] = Query(None, description="Inclusive"),
    fecha_hasta: Optional[date] = Query(None, description="Inclusive"),
    categoria: Optional[CategoriaObjeto] = Query(None),
    estado: Optional[str] = Query(None, description="Estado del registro (no aplica a 'entregas')"),
    entidad: Optional[str] = Query(None, description="Solo 'auditoria': tipo de entidad"),
    accion: Optional[AccionAuditoria] = Query(None, description="Solo 'auditoria': acción"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Informe descargable de la sede. `entregas` reúne las actas de entrega con los
    datos del reclamante y del objeto (soporte ante las directivas); los otros tres
    son el inventario, los reportes de pérdida y las publicaciones de encontrados.
    Máximo 10.000 filas por archivo."""
    assert recurso in RECURSOS_EXPORTABLES or recurso == "auditoria"
    _validar_fechas(fecha_desde, fecha_hasta)
    if recurso == "auditoria":
        columnas, filas = _datos_auditoria(
            db, current_admin.sede_id, fecha_desde, fecha_hasta, entidad, accion
        )
    else:
        columnas, filas = AnaliticaCRUD(db).datos_exportacion(
            recurso,
            current_admin.sede_id,
            fecha_desde,
            fecha_hasta,
            categoria.value if categoria else None,
            estado,
        )
    nombre = f"{recurso}_{date.today().isoformat()}.{formato}"
    if formato == "csv":
        cuerpo, tipo = a_csv(columnas, filas), "text/csv; charset=utf-8"
    else:
        cuerpo, tipo = a_xlsx(columnas, filas, recurso.replace("-", " ").title()), XLSX
    return Response(
        content=cuerpo,
        media_type=tipo,
        headers={
            "Content-Disposition": f'attachment; filename="{nombre}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
