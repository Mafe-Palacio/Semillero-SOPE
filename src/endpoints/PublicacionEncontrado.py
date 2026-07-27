"""
Endpoint de Publicaciones Encontradas
"""

import traceback
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user, get_current_admin_con_sede
from src.crud.PublicacionEncontrado_crud import PublicacionEncontradoCRUD
from src.crud.PuntoEntrega_crud import PuntoEntregaCRUD
from src.database.config import get_db
from src.entities.PublicacionEncontrado import PublicacionEncontrado
from src.schemas.PublicacionEncontradoSchema import (
    PublicacionEncontradoCreate,
    PublicacionEncontradoModeracion,
    PublicacionEncontradoResolverEliminacion,
    PublicacionEncontradoResponse,
    PublicacionEncontradoUpdate,
)

router = APIRouter(
    prefix="/publicaciones-encontradas",
    tags=["Publicaciones Encontradas"],
    dependencies=[Depends(get_current_user)],
)


def _verificar_sede_admin(
    publicacion: PublicacionEncontrado, current_admin, db: Session
) -> None:
    """La sede que gobierna la administración es la del punto de ENTREGA
    (donde el objeto queda físicamente en custodia), no la del hallazgo."""
    punto = PuntoEntregaCRUD(db).obtener_punto_entrega_por_id(
        publicacion.lugar_entrega_fisica_id
    )
    if not punto or punto.sede_id != current_admin.sede_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso sobre publicaciones de otra sede",
        )


@router.post(
    "/",
    response_model=PublicacionEncontradoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_publicacion_encontrada(
    data: PublicacionEncontradoCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        crud = PublicacionEncontradoCRUD(db)
        return crud.crear_publicacion_encontrada(
            usuario_id=current_user.id_usuario,
            categoria=data.categoria.value,
            descripcion=data.descripcion,
            lugar_hallazgo_id=data.lugar_hallazgo_id,
            lugar_entrega_fisica_id=data.lugar_entrega_fisica_id,
            fecha_hallazgo=data.fecha_hallazgo,
            imagen_url=data.imagen_url,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la publicación: {str(e)}",
        )


@router.get("/me", response_model=List[PublicacionEncontradoResponse])
async def obtener_mis_publicaciones(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    crud = PublicacionEncontradoCRUD(db)
    return crud.obtener_publicaciones_encontradas_por_usuario(
        usuario_id=current_user.id_usuario, skip=skip, limit=limit
    )


@router.get("/buscar", response_model=List[PublicacionEncontradoResponse])
async def buscar_publicaciones_por_sede_hallazgo(
    sede_id: UUID = Query(..., description="Sede donde se busca el objeto encontrado"),
    categoria: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Búsqueda pública (cualquier usuario autenticado): objetos APROBADOS
    encontrados en una sede — para que alguien que perdió algo en Robledo
    revise qué ha aparecido ahí, sin importar a qué oficina fue entregado.
    """
    try:
        crud = PublicacionEncontradoCRUD(db)
        return crud.buscar_publicaciones_encontradas_por_sede_hallazgo(
            sede_id=sede_id, categoria=categoria, skip=skip, limit=limit
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al buscar publicaciones: {str(e)}",
        )


@router.get("/", response_model=List[PublicacionEncontradoResponse])
async def obtener_publicaciones_encontradas(
    usuario_id: Optional[UUID] = Query(None),
    categoria: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    lugar_hallazgo_id: Optional[UUID] = Query(None),
    puntoEntrega_id: Optional[UUID] = Query(None),
    eliminacion_solicitada: Optional[bool] = Query(None),
    fecha_hallazgo_desde: Optional[date] = Query(None),
    fecha_hallazgo_hasta: Optional[date] = Query(None),
    fecha_edicion_desde: Optional[datetime] = Query(None),
    fecha_edicion_hasta: Optional[datetime] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """
    Bandeja administrativa, siempre acotada a la sede del punto de entrega
    del admin autenticado. Todos los filtros se combinan entre sí.
    """
    try:
        crud = PublicacionEncontradoCRUD(db)
        return crud.obtener_publicaciones_encontradas_admin(
            sede_id=current_admin.sede_id,
            usuario_id=usuario_id,
            categoria=categoria,
            estado=estado,
            lugar_hallazgo_id=lugar_hallazgo_id,
            puntoEntrega_id=puntoEntrega_id,
            eliminacion_solicitada=eliminacion_solicitada,
            fecha_hallazgo_desde=fecha_hallazgo_desde,
            fecha_hallazgo_hasta=fecha_hallazgo_hasta,
            fecha_edicion_desde=fecha_edicion_desde,
            fecha_edicion_hasta=fecha_edicion_hasta,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las publicaciones: {str(e)}",
        )


@router.get("/{publicacion_id}", response_model=PublicacionEncontradoResponse)
async def obtener_publicacion_encontrada(
    publicacion_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """El dueño de la publicación o un ADMIN de su sede de entrega pueden verla."""
    crud = PublicacionEncontradoCRUD(db)
    publicacion = crud.obtener_publicacion_encontrada_por_id(publicacion_id)

    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada",
        )

    es_dueno = publicacion.usuario_id == current_user.id_usuario
    if not es_dueno:
        if current_user.rol != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver esta publicación",
            )
        _verificar_sede_admin(publicacion, current_user, db)

    return publicacion


@router.put("/{publicacion_id}", response_model=PublicacionEncontradoResponse)
async def editar_publicacion_encontrada(
    publicacion_id: UUID,
    data: PublicacionEncontradoUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Corrección administrativa de categoría/descripción/imagen (HU07)."""
    try:
        crud = PublicacionEncontradoCRUD(db)
        publicacion = crud.obtener_publicacion_encontrada_por_id(publicacion_id)
        if not publicacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publicación no encontrada",
            )

        _verificar_sede_admin(publicacion, current_admin, db)

        campos = {k: v for k, v in data.model_dump().items() if v is not None}
        if not campos:
            return publicacion

        return crud.editar_publicacion_encontrada(
            publicacionEncontrado_id=publicacion_id,
            usuario_edita_id=current_admin.id_usuario,
            **campos,
        )

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al editar la publicación: {str(e)}",
        )


@router.put(
    "/{publicacion_id}/moderacion", response_model=PublicacionEncontradoResponse
)
async def moderar_publicacion_encontrada(
    publicacion_id: UUID,
    data: PublicacionEncontradoModeracion,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Aprueba o rechaza la publicación (HU02)."""
    try:
        crud = PublicacionEncontradoCRUD(db)
        publicacion = crud.obtener_publicacion_encontrada_por_id(publicacion_id)
        if not publicacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publicación no encontrada",
            )

        _verificar_sede_admin(publicacion, current_admin, db)

        if data.estado == "APROBADA":
            return crud.aprobar_publicacion_encontrada(publicacion_id)

        if data.estado == "RECHAZADA":
            if not data.motivo_rechazo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El motivo de rechazo es obligatorio",
                )
            return crud.rechazar_publicacion_encontrada(
                publicacion_id, data.motivo_rechazo
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado de moderación inválido; use 'APROBADA' o 'RECHAZADA'",
        )

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al moderar la publicación: {str(e)}",
        )


@router.put(
    "/{publicacion_id}/solicitar-eliminacion",
    response_model=PublicacionEncontradoResponse,
)
async def solicitar_eliminacion_publicacion(
    publicacion_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Solo el dueño de la publicación puede solicitar su eliminación."""
    crud = PublicacionEncontradoCRUD(db)
    publicacion = crud.obtener_publicacion_encontrada_por_id(publicacion_id)

    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada",
        )

    if publicacion.usuario_id != current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el autor de la publicación puede solicitar su eliminación",
        )

    return crud.solicitar_eliminacion_publicacion_encontrada(publicacion_id)


@router.put(
    "/{publicacion_id}/resolver-eliminacion",
    response_model=Optional[PublicacionEncontradoResponse],
)
async def resolver_eliminacion_publicacion(
    publicacion_id: UUID,
    data: PublicacionEncontradoResolverEliminacion,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_con_sede),
):
    """Admin aprueba (borra definitivamente) o rechaza (restaura a APROBADA)
    la solicitud de eliminación hecha por el usuario."""
    try:
        crud = PublicacionEncontradoCRUD(db)
        publicacion = crud.obtener_publicacion_encontrada_por_id(publicacion_id)
        if not publicacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publicación no encontrada",
            )

        _verificar_sede_admin(publicacion, current_admin, db)

        return crud.resolver_solicitud_eliminacion_publicacion(
            publicacionEncontrado_id=publicacion_id,
            aprobar=data.aprobar,
            motivo=data.motivo,
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al resolver la solicitud de eliminación: {str(e)}",
        )
