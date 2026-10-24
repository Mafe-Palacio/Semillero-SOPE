"""
POST /imagenes - Carga validada de imágenes (HU28).
"""

import traceback

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from src.core.auth import CurrentUser, get_current_user
from src.core.config import get_settings
from src.schemas.ImagenSchema import ImagenSubidaResponse
from src.utils.imagenes import (
    MAX_BYTES_IMAGEN,
    ImagenInvalidaError,
    subir_a_cloudinary,
    validar_imagen,
)

router = APIRouter(prefix="/imagenes", tags=["Imágenes"])


@router.post(
    "", response_model=ImagenSubidaResponse, status_code=status.HTTP_201_CREATED
)
async def subir_imagen(
    archivo: UploadFile = File(..., description="Imagen JPG, JPEG o PNG de máximo 5 MB"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Valida formato (JPG/PNG) y tamaño (5 MB), sube la imagen a Cloudinary y
    devuelve la URL para usarla en `imagen_url`, `evidencia_url` o `firma_url`."""
    settings = get_settings()
    # Se lee un byte de más para detectar que excede el límite sin cargar archivos enormes.
    datos = await archivo.read(MAX_BYTES_IMAGEN + 1)
    try:
        formato = validar_imagen(archivo.content_type, datos)
    except ImagenInvalidaError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    try:
        resultado = await run_in_threadpool(
            subir_a_cloudinary, datos, "ope", settings
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo subir la imagen: {e}",
        )

    return ImagenSubidaResponse(
        url=resultado["secure_url"], formato=formato, bytes=len(datos)
    )
