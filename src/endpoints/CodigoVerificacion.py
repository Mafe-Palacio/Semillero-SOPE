"""
Endpoint de CodigoVerificacion

Solo expone lectura (GET), restringida a ADMIN, para soporte y auditoría.
"""

import traceback
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_admin
from src.crud.CodigoVerificacion_crud import CodigoVerificacionCRUD
from src.database.config import get_db
from src.schemas.CodigoVerificacionSchema import CodigoVerificacionResponse

router = APIRouter(
    prefix="/codigos-verificacion",
    tags=["Códigos de Verificación"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/", response_model=List[CodigoVerificacionResponse])
async def obtener_todos_codigos_verificacion(
    usuario_id: Optional[UUID] = Query(None, description="Filtrar por usuario"),
    tipo: Optional[str] = Query(
        None, description="Filtrar por tipo ('REGISTRO', 'RECUPERACION_PASSWORD')"
    ),
    usado: Optional[bool] = Query(
        None, description="Filtra por estado de consumo (usado/pendiente)"
    ),
    expira_desde: Optional[datetime] = Query(
        None, description="Rango de expiración: inicio"
    ),
    expira_hasta: Optional[datetime] = Query(
        None, description="Rango de expiración: fin"
    ),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Listado de códigos de verificación, solo para soporte/auditoría (ADMIN).

    Orden de precedencia si mandan varios filtros a la vez:
    rango de expiración > usuario > tipo > usado.
    """
    try:
        crud = CodigoVerificacionCRUD(db)

        if expira_desde and expira_hasta:
            return crud.obtener_codigos_verificacion_por_rango_expiracion(
                fecha_inicio=expira_desde,
                fecha_fin=expira_hasta,
                skip=skip,
                limit=limit,
            )

        if usuario_id:
            return crud.obtener_codigos_verificacion_por_usuario(
                usuario_id=usuario_id, skip=skip, limit=limit
            )

        if tipo:
            return crud.obtener_codigos_verificacion_por_tipo(
                tipo=tipo, skip=skip, limit=limit
            )

        if usado is not None:
            return crud.obtener_codigos_verificacion_por_usado(
                usado=usado, skip=skip, limit=limit
            )

        return crud.obtener_codigos_verificacion(skip=skip, limit=limit)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener los códigos de verificación: {str(e)}",
        )


@router.get("/usuario/{usuario_id}/vigente", response_model=CodigoVerificacionResponse)
async def obtener_codigo_vigente_de_usuario(
    usuario_id: UUID,
    tipo: str = Query(
        ..., description="Tipo de código ('REGISTRO' o 'RECUPERACION_PASSWORD')"
    ),
    db: Session = Depends(get_db),
):
    """Consulta rápida de soporte: ¿tiene este usuario un código vigente
    (no usado, sin importar si ya expiró) de este tipo ahora mismo?"""
    try:
        crud = CodigoVerificacionCRUD(db)
        codigo = crud.obtener_ultimo_codigo_vigente(usuario_id=usuario_id, tipo=tipo)

        if not codigo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario no tiene un código pendiente de este tipo",
            )

        return codigo

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el código vigente: {str(e)}",
        )


@router.get("/{codigoVerificacion_id}", response_model=CodigoVerificacionResponse)
async def obtener_codigo_verificacion(
    codigoVerificacion_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        crud = CodigoVerificacionCRUD(db)
        codigo = crud.obtener_codigo_verificacion_por_id(codigoVerificacion_id)

        if not codigo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Código de verificación no encontrado",
            )

        return codigo

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el código de verificación: {str(e)}",
        )
