from uuid import UUID
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.entities.ActaEntrega import ActaEntrega


class ActaEntregaCRUD:
    """Clase encargada de las operaciones de base de datos para ActaEntrega."""

    def __init__(self, db: Session):
        self.db = db

    def crear_acta(
        self,
        reclamo_id: UUID,
        nombre_reclamante: str,
        cedula_reclamante: str,
        correo_reclamante: str,
        celular_reclamante: str,
        carnet_reclamante: str,
        firma_url: str,
        validacion_verbal: bool,
        procesada_por_admin_id: UUID,
    ) -> ActaEntrega:
        """Crea un registro de acta de entrega en la base de datos."""

        nueva_acta = ActaEntrega(
            reclamo_id=reclamo_id,
            nombre_reclamante=nombre_reclamante,
            cedula_reclamante=cedula_reclamante,
            correo_reclamante=correo_reclamante,
            celular_reclamante=celular_reclamante,
            carnet_reclamante=carnet_reclamante,
            firma_url=firma_url,
            validacion_verbal=validacion_verbal,
            procesada_por_admin_id=procesada_por_admin_id,
            fecha_hora_entrega=datetime.utcnow(),
        )

        try:
            self.db.add(nueva_acta)
            self.db.commit()
            self.db.refresh(nueva_acta)
            return nueva_acta
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Ya existe un acta de entrega para este reclamo.")

    def obtener_acta_por_id(self, actaEntrega_id: UUID) -> Optional[ActaEntrega]:
        """Busca un acta usando su identificador único."""
        return (
            self.db.query(ActaEntrega)
            .filter(ActaEntrega.actaEntrega_id == actaEntrega_id)
            .first()
        )

    def obtener_acta_por_reclamo(self, reclamo_id: UUID) -> Optional[ActaEntrega]:
        """Obtiene el acta correspondiente a un reclamo específico (1:1)."""
        return (
            self.db.query(ActaEntrega)
            .filter(ActaEntrega.reclamo_id == reclamo_id)
            .first()
        )

    def obtener_todas_las_actas(
        self, skip: int = 0, limit: int = 100
    ) -> List[ActaEntrega]:
        """Obtiene un historial de todas las actas registradas en el sistema."""
        return (
            self.db.query(ActaEntrega)
            .order_by(ActaEntrega.fecha_hora_entrega.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
