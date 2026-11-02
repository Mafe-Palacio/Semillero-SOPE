from uuid import UUID
from typing import List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.entities.ActaEntrega import ActaEntrega
from src.entities.Reclamos import Reclamo
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

    def listar_de_sede(
        self,
        sede_id: UUID,
        *,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        reclamo_id: Optional[UUID] = None,
        procesada_por: Optional[UUID] = None,
        validacion_verbal: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ):
        """Actas de entrega de la sede, más recientes primero. Devuelve (actas, total)."""
        consulta = (
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
            .filter(PuntoEntrega.sede_id == sede_id)
        )
        if fecha_desde:
            consulta = consulta.filter(
                ActaEntrega.fecha_hora_entrega
                >= datetime.combine(fecha_desde, datetime.min.time())
            )
        if fecha_hasta:  # inclusiva
            consulta = consulta.filter(
                ActaEntrega.fecha_hora_entrega
                < datetime.combine(fecha_hasta + timedelta(days=1), datetime.min.time())
            )
        if reclamo_id:
            consulta = consulta.filter(ActaEntrega.reclamo_id == reclamo_id)
        if procesada_por:
            consulta = consulta.filter(ActaEntrega.procesada_por_admin_id == procesada_por)
        if validacion_verbal is not None:
            consulta = consulta.filter(ActaEntrega.validacion_verbal == validacion_verbal)

        total = consulta.count()
        actas = (
            consulta.order_by(ActaEntrega.fecha_hora_entrega.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return actas, total
