from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class CategoriaIncidencia(BaseModel):
    categoria: str
    total: int


class PendientesAprobacion(BaseModel):
    reportes_perdida: int = 0
    publicaciones_encontradas: int = 0
    solicitudes_eliminacion: int = 0


class MetricasResumen(BaseModel):
    """Indicadores del dashboard (HU12 / CU19) de una sede."""

    total_objetos: int
    objetos_por_estado: Dict[str, int]
    reclamados: int
    sin_reclamar: int  # EN_CUSTODIA + POR_VENCER + SIN_DUENO_DEFINITIVO
    sin_dueno_definitivo: int
    porcentaje_devueltos: float
    dias_promedio_custodia: Optional[float] = None  # solo objetos ya entregados
    categorias_mas_perdidas: List[CategoriaIncidencia]
    reclamos_por_estado: Dict[str, int]
    pendientes_aprobacion: PendientesAprobacion
    generado_en: datetime
