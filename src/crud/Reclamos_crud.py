from uuid import UUID
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from src.entities.Reclamos import Reclamo
from src.entities.Enums import EstadoReclamo
from src.entities.ObjetoEnCustodia import ObjetoEnCustodia
from src.entities.PuntoEntrega import PuntoEntrega


class ReclamoCRUD:
    def __init__(self, db: Session):
        self.db = db

    def crear_reclamo(
        self,
        objetoEnCustodia_id: UUID,
        usuario_id: UUID,
        es_presencial: bool,
        evidencia_url: Optional[str] = None,
    ) -> Reclamo:
        nuevo_reclamo = Reclamo(
            objetoEnCustodia_id=objetoEnCustodia_id,
            usuario_id=usuario_id,
            es_presencial=es_presencial,
            evidencia_url=evidencia_url,
            estado=EstadoReclamo.ENVIADO,
            fecha_envio=datetime.utcnow(),
        )
        self.db.add(nuevo_reclamo)
        self.db.commit()
        self.db.refresh(nuevo_reclamo)
        return nuevo_reclamo

    def obtener_reclamo_de_sede_o_404(self, reclamo_id: UUID, sede_id: UUID) -> Reclamo:
        """Filtra el reclamo validando la sede mediante JOINs."""
        reclamo = (
            self.db.query(Reclamo)
            .join(
                ObjetoEnCustodia,
                Reclamo.objetoEnCustodia_id == ObjetoEnCustodia.objetoEnCustodia_id,
            )
            .join(
                PuntoEntrega,
                ObjetoEnCustodia.lugar_origen_id == PuntoEntrega.puntoEntrega_id,
            )
            .filter(Reclamo.reclamo_id == reclamo_id, PuntoEntrega.sede_id == sede_id)
            .first()
        )
        if not reclamo:
            raise ValueError("Reclamo no encontrado o no pertenece a tu sede.")
        return reclamo

    def obtener_reclamos_por_usuario(
        self, usuario_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Reclamo]:
        return (
            self.db.query(Reclamo)
            .filter(Reclamo.usuario_id == usuario_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def actualizar_reclamo(self, reclamo_id: UUID, **kwargs) -> Optional[Reclamo]:
        reclamo = (
            self.db.query(Reclamo).filter(Reclamo.reclamo_id == reclamo_id).first()
        )
        if not reclamo:
            return None
        for key, value in kwargs.items():
            if hasattr(reclamo, key) and value is not None:
                setattr(reclamo, key, value)
        self.db.commit()
        self.db.refresh(reclamo)
        return reclamo
