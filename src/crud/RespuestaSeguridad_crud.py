from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from src.entities.RespuestaSeguridad import RespuestaSeguridad


class RespuestaSeguridadCRUD:
    """Clase para manejar las operaciones de base de datos de RespuestaSeguridad."""

    def __init__(self, db: Session):
        self.db = db

    def crear_respuesta(
        self,
        reclamo_id: UUID,
        preguntaSeguridad_id: UUID,
        respuesta_usuario: str,
    ) -> RespuestaSeguridad:
        """Guarda una nueva respuesta en la base de datos."""
        nueva_respuesta = RespuestaSeguridad(
            reclamo_id=reclamo_id,
            preguntaSeguridad_id=preguntaSeguridad_id,
            respuesta_usuario=respuesta_usuario,
        )

        self.db.add(nueva_respuesta)
        self.db.commit()
        self.db.refresh(nueva_respuesta)
        return nueva_respuesta

    def obtener_respuesta_por_id(
        self, respuestaSeguridad_id: UUID
    ) -> Optional[RespuestaSeguridad]:
        """Busca una respuesta específica usando su ID."""
        return (
            self.db.query(RespuestaSeguridad)
            .filter(RespuestaSeguridad.respuestaSeguridad_id == respuestaSeguridad_id)
            .first()
        )

    def obtener_respuestas_por_reclamo(
        self, reclamo_id: UUID
    ) -> List[RespuestaSeguridad]:
        """Obtiene todas las respuestas asociadas a un reclamo en particular."""
        return (
            self.db.query(RespuestaSeguridad)
            .filter(RespuestaSeguridad.reclamo_id == reclamo_id)
            .all()
        )

    def actualizar_respuesta(
        self, respuestaSeguridad_id: UUID, respuesta_usuario: str
    ) -> Optional[RespuestaSeguridad]:
        """Actualiza el texto de una respuesta existente."""
        respuesta = self.obtener_respuesta_por_id(respuestaSeguridad_id)
        if not respuesta:
            return None

        respuesta.respuesta_usuario = respuesta_usuario

        self.db.commit()
        self.db.refresh(respuesta)
        return respuesta

    def eliminar_respuesta(self, respuestaSeguridad_id: UUID) -> bool:
        """Elimina una respuesta de la base de datos."""
        respuesta = self.obtener_respuesta_por_id(respuestaSeguridad_id)
        if not respuesta:
            return False

        self.db.delete(respuesta)
        self.db.commit()
        return True
