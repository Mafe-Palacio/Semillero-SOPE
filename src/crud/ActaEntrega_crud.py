from uuid import UUID
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.entities.ActaEntrega import ActaEntrega
from src.entities.Reclamo import Reclamo
from src.entities.ObjetoEnCustodia import ObjetoEnCustodia
from src.entities.PuntoEntrega import PuntoEntrega


class ActaEntregaCRUD:
    def __init__(self, db: Session):
        self.db = db

    def crear_acta(self, **kwargs) -> ActaEntrega:
        nueva_acta = ActaEntrega(**kwargs, fecha_hora_entrega=datetime.utcnow())
        try:
            self.db.add(nueva_acta)
            self.db.commit()
            self.db.refresh(nueva_acta)
            return nueva_acta
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Ya existe un acta de entrega para este reclamo.")

    def obtener_acta_de_sede_o_404(
        self, actaEntrega_id: UUID, sede_id: UUID
    ) -> ActaEntrega:
        acta = (
            self.db.query(ActaEntrega)
            .join(Reclamo, ActaEntrega.reclamo_id == Reclamo.reclamo_id)
            .join(
                ObjetoEnCustodia,
                Reclamo.objetoEnCustodia_id == ObjetoEnCustodia.objetoEnCustodia_id,
            )
            .join(
                PuntoEntrega,
                ObjetoEnCustodia.lugar_origen_id == PuntoEntrega.puntoEntrega_id,
            )
            .filter(
                ActaEntrega.actaEntrega_id == actaEntrega_id,
                PuntoEntrega.sede_id == sede_id,
            )
            .first()
        )
        if not acta:
            raise ValueError("Acta no encontrada o no pertenece a tu sede.")
        return acta
