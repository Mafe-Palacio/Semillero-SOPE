"""
Validación y carga de imágenes (HU28, CU06/CU07).

Reglas: solo JPG/JPEG o PNG, máximo 5 MB, y el contenido real del archivo debe
coincidir con el tipo declarado (firma "magic bytes"), no solo la extensión.
La carga se hace a Cloudinary; la API solo guarda la URL resultante.
"""

from typing import Annotated, Optional
from urllib.parse import urlparse

from pydantic import AfterValidator

from src.core.config import Settings

MAX_BYTES_IMAGEN = 5 * 1024 * 1024  # 5 MB
TIPOS_PERMITIDOS = {"image/jpeg": "jpg", "image/jpg": "jpg", "image/png": "png"}

_PNG = b"\x89PNG\r\n\x1a\n"
_JPEG = b"\xff\xd8\xff"


class ImagenInvalidaError(ValueError):
    """La imagen no cumple formato o tamaño. `status_code` indica el HTTP sugerido."""

    def __init__(self, mensaje: str, status_code: int = 400):
        super().__init__(mensaje)
        self.status_code = status_code


def validar_imagen(content_type: Optional[str], data: bytes) -> str:
    """Valida tipo, tamaño y contenido. Devuelve el formato ('jpg' o 'png')."""
    tipo = (content_type or "").split(";")[0].strip().lower()
    formato = TIPOS_PERMITIDOS.get(tipo)
    if formato is None:
        raise ImagenInvalidaError(
            "Formato no permitido: solo se aceptan imágenes JPG, JPEG o PNG", 415
        )
    if len(data) == 0:
        raise ImagenInvalidaError("El archivo está vacío", 400)
    if len(data) > MAX_BYTES_IMAGEN:
        raise ImagenInvalidaError("La imagen supera el límite de 5 MB", 413)
    es_png = data.startswith(_PNG)
    es_jpg = data.startswith(_JPEG)
    if (formato == "png" and not es_png) or (formato == "jpg" and not es_jpg):
        raise ImagenInvalidaError(
            "El contenido del archivo no corresponde a una imagen JPG o PNG válida", 415
        )
    return formato


def subir_a_cloudinary(data: bytes, carpeta: str, settings: Settings) -> dict:
    """Sube los bytes a Cloudinary y devuelve la respuesta del SDK."""
    if not (
        settings.cloudinary_cloud_name
        and settings.cloudinary_api_key
        and settings.cloudinary_api_secret
    ):
        raise RuntimeError("Cloudinary no está configurado")
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    return cloudinary.uploader.upload(data, folder=carpeta, resource_type="image")


def validar_url_imagen(valor: Optional[str]) -> Optional[str]:
    """Las URL de imagen deben ser https y, si IMAGE_ALLOWED_HOSTS está definida,
    pertenecer a uno de esos hosts (p. ej. res.cloudinary.com)."""
    if valor is None:
        return None
    from src.core.config import get_settings

    url = valor.strip()
    partes = urlparse(url)
    if partes.scheme != "https" or not partes.netloc:
        raise ValueError("La URL de la imagen debe ser https")
    permitidos = get_settings().image_allowed_hosts_list()
    if permitidos and (partes.hostname or "").lower() not in permitidos:
        raise ValueError("La imagen debe subirse mediante POST /imagenes")
    return url


UrlImagen = Annotated[Optional[str], AfterValidator(validar_url_imagen)]
UrlImagenRequerida = Annotated[str, AfterValidator(validar_url_imagen)]
