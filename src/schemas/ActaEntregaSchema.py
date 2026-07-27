from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


class ActaEntregaBase(BaseModel):
    """Atributos principales que se necesitan para generar un acta de entrega."""

    reclamo_id: UUID
    nombre_reclamante: str
    cedula_reclamante: str
    correo_reclamante: EmailStr  # Pydantic validará que tenga formato de correo
    celular_reclamante: str
    carnet_reclamante: str
    firma_url: str
    validacion_verbal: bool


class ActaEntregaCreate(ActaEntregaBase):
    """Datos requeridos al momento de guardar el acta.
    Nota: procesada_por_admin_id lo tomaremos del token del usuario logueado en el endpoint.
    """

    pass


class ActaEntregaResponse(ActaEntregaBase):
    """Respuesta que devuelve la API con toda la información del acta."""

    actaEntrega_id: UUID
    fecha_hora_entrega: datetime
    procesada_por_admin_id: UUID

    model_config = ConfigDict(from_attributes=True)
