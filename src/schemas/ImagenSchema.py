from pydantic import BaseModel


class ImagenSubidaResponse(BaseModel):
    """Resultado de una carga de imagen validada."""

    url: str
    formato: str
    bytes: int
