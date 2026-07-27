from uuid import UUID
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from src.entities.Reclamos import Reclamo, EstadoReclamo


class ReclamoCRUD:
    """CRUD de la entidad Reclamo para gestionar solicitudes de objetos."""

    def __init__(self, db: Session):
        self.db = db

    def crear_reclamo(
        self,
        objetoEnCustodia_id: UUID,
        usuario_id: UUID,
        es_presencial: bool,
        evidencia_url: Optional[str] = None,
    ) -> Reclamo:
        """Crea un nuevo reclamo en estado PENDIENTE."""

        nuevo_reclamo = Reclamo(
            objetoEnCustodia_id=objetoEnCustodia_id,
            usuario_id=usuario_id,
            es_presencial=es_presencial,
            evidencia_url=evidencia_url,
            estado=EstadoReclamo.PENDIENTE,
            fecha_envio=datetime.utcnow(),
        )

        self.db.add(nuevo_reclamo)
        self.db.commit()
        self.db.refresh(nuevo_reclamo)
        return nuevo_reclamo

    def obtener_reclamo_por_id(self, reclamo_id: UUID) -> Optional[Reclamo]:
        """Obtiene un reclamo específico por su ID."""
        return self.db.query(Reclamo).filter(Reclamo.reclamo_id == reclamo_id).first()

    def obtener_reclamos_por_usuario(
        self, usuario_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Reclamo]:
        """Obtiene todos los reclamos realizados por un usuario específico."""
        return (
            self.db.query(Reclamo)
            .filter(Reclamo.usuario_id == usuario_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def actualizar_reclamo(self, reclamo_id: UUID, **kwargs) -> Optional[Reclamo]:
        """Actualiza atributos específicos de un reclamo (ej. estado, cita)."""
        reclamo = self.obtener_reclamo_por_id(reclamo_id)
        if not reclamo:
            return None

        for key, value in kwargs.items():
            if hasattr(reclamo, key) and value is not None:
                setattr(reclamo, key, value)

        self.db.commit()
        self.db.refresh(reclamo)
        return reclamo

    def eliminar_reclamo(self, reclamo_id: UUID) -> bool:
        """Elimina un reclamo por su ID."""
        reclamo = self.obtener_reclamo_por_id(reclamo_id)
        if not reclamo:
            return False

        self.db.delete(reclamo)
        self.db.commit()
        return True
