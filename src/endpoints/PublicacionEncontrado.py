"""
Endpoint de Publicaciones Encontradas
"""

from typing import List
from uuid import UUID
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user
from src.crud.PublicacionEncontrado_crud import PublicacionEncontradoCRUD
from src.database.config import get_db
from src.schemas.PublicacionEncontradoSchema import (
    PublicacionEncontradoCreate,
    PublicacionEncontradoResponse,
    PublicacionEncontradoUpdate,
)
from src.schemas.schemas import RespuestaAPI

router = APIRouter(
    prefix="/publicaciones-encontradas",
    tags=["Publicaciones Encontradas"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=List[PublicacionEncontradoResponse])
async def obtener_todas_publicaciones(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    try:
        crud = PublicacionEncontradoCRUD(db)
        return crud.obtener_todas_publicaciones(skip=skip, limit=limit)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las publicaciones: {str(e)}",
        )


@router.get("/{publicacion_id}", response_model=PublicacionEncontradoResponse)
async def obtener_publicacion(
    publicacion_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        crud = PublicacionEncontradoCRUD(db)

        publicacion = crud.obtener_publicacion(publicacion_id)

        if not publicacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publicación no encontrada",
            )

        return publicacion

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la publicación: {str(e)}",
        )


@router.get("/usuario/{usuario_id}", response_model=List[PublicacionEncontradoResponse])
async def obtener_publicaciones_usuario(
    usuario_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        crud = PublicacionEncontradoCRUD(db)

        return crud.obtener_publicaciones_por_usuario(usuario_id)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las publicaciones del usuario: {str(e)}",
        )


@router.get(
    "/categoria/{categoria}", response_model=List[PublicacionEncontradoResponse]
)
async def obtener_publicaciones_categoria(
    categoria: str,
    db: Session = Depends(get_db),
):
    try:
        crud = PublicacionEncontradoCRUD(db)

        return crud.obtener_publicaciones_por_categoria(categoria)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las publicaciones: {str(e)}",
        )


@router.get("/estado/{estado}", response_model=List[PublicacionEncontradoResponse])
async def obtener_publicaciones_estado(
    estado: str,
    db: Session = Depends(get_db),
):
    try:
        crud = PublicacionEncontradoCRUD(db)

        return crud.obtener_publicaciones_por_estado(estado)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las publicaciones: {str(e)}",
        )


@router.post(
    "",
    response_model=PublicacionEncontradoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_publicacion(
    publicacion_data: PublicacionEncontradoCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        crud = PublicacionEncontradoCRUD(db)

        publicacion = crud.crear_publicacion(
            usuario_id=publicacion_data.usuario_id,
            categoria=publicacion_data.categoria,
            descripcion=publicacion_data.descripcion,
            lugar_hallado=publicacion_data.lugar_hallado,
            fecha_hallazgo=publicacion_data.lugar_hallado,
            lugar_entrega=publicacion_data.lugar_entrega,
            imagen_url=publicacion_data.imagen_url,
            estado=publicacion_data.estado,
            id_usuario_crea=current_user.id_usuario,
        )

        return publicacion

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la publicación: {str(e)}",
        )


@router.put("/{publicacion_id}", response_model=PublicacionEncontradoResponse)
async def actualizar_publicacion(
    publicacion_id: UUID,
    publicacion_data: PublicacionEncontradoUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        crud = PublicacionEncontradoCRUD(db)

        publicacion_existente = crud.obtener_publicacion(publicacion_id)

        if not publicacion_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publicación no encontrada",
            )

        campos_actualizacion = {
            k: v for k, v in publicacion_data.dict().items() if v is not None
        }

        if not campos_actualizacion:
            return publicacion_existente

        publicacion_actualizada = crud.actualizar_publicacion(
            publicacion_id=publicacion_id,
            id_usuario_edita=current_user.id_usuario,
            **campos_actualizacion,
        )

        return publicacion_actualizada

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la publicación: {str(e)}",
        )


@router.delete("/{publicacion_id}", response_model=RespuestaAPI)
async def eliminar_publicacion(
    publicacion_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        crud = PublicacionEncontradoCRUD(db)

        publicacion = crud.obtener_publicacion(publicacion_id)

        if not publicacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publicación no encontrada",
            )

        eliminado = crud.eliminar_publicacion(publicacion_id)

        if eliminado:
            return RespuestaAPI(
                mensaje="Publicación eliminada exitosamente",
                exito=True,
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar la publicación",
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la publicación: {str(e)}",
        )
