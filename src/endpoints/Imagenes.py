"""
POST /imagenes - Carga validada de imágenes (HU28).
Incluye almacenamiento local en `uploads/` cuando Cloudinary no está configurado en `.env`.
"""

from pathlib import Path
import re
import traceback
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

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

UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads"
_NOMBRE_SEGURO_RE = re.compile(r"^[a-f0-9]{32}\.(jpg|png)$")


@router.post(
    "", response_model=ImagenSubidaResponse, status_code=status.HTTP_201_CREATED
)
async def subir_imagen(
    request: Request,
    archivo: UploadFile = File(..., description="Imagen JPG, JPEG o PNG de máximo 5 MB"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Valida formato (JPG/PNG) y tamaño (5 MB), sube la imagen a Cloudinary
    (o la guarda localmente si Cloudinary no está configurado) y devuelve la URL
    para usarla en `imagen_url`, `evidencia_url` o `firma_url`."""
    settings = get_settings()
    # Se lee un byte de más para detectar que excede el límite sin cargar archivos enormes.
    datos = await archivo.read(MAX_BYTES_IMAGEN + 1)
    try:
        formato = validar_imagen(archivo.content_type, datos)
    except ImagenInvalidaError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    tiene_cloudinary = bool(
        settings.cloudinary_cloud_name
        and settings.cloudinary_api_key
        and settings.cloudinary_api_secret
    )

    if tiene_cloudinary:
        try:
            resultado = await run_in_threadpool(
                subir_a_cloudinary, datos, "ope", settings
            )
            return ImagenSubidaResponse(
                url=resultado["secure_url"], formato=formato, bytes=len(datos)
            )
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"No se pudo subir la imagen: {e}",
            )

    # Almacenamiento local seguro cuando Cloudinary no está configurado
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    nombre_archivo = f"{uuid4().hex}.{formato}"
    ruta_archivo = UPLOADS_DIR / nombre_archivo
    await run_in_threadpool(ruta_archivo.write_bytes, datos)

    base_url = str(request.base_url).rstrip("/")
    url_publica = f"{base_url}/imagenes/{nombre_archivo}"
    return ImagenSubidaResponse(
        url=url_publica, formato=formato, bytes=len(datos)
    )


@router.get("/{nombre_archivo}", include_in_schema=False)
async def obtener_imagen_local(nombre_archivo: str):
    """Sirve las imágenes almacenadas localmente en `uploads/`."""
    if not _NOMBRE_SEGURO_RE.match(nombre_archivo):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagen no encontrada")
    ruta = UPLOADS_DIR / nombre_archivo
    if not ruta.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagen no encontrada")
    media_type = "image/png" if nombre_archivo.endswith(".png") else "image/jpeg"
    return FileResponse(
        ruta,
        media_type=media_type,
        headers={"Cross-Origin-Resource-Policy": "cross-origin"},
    )
