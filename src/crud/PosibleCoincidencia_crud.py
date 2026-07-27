from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from src.entities.PosibleCoincidencia import PosibleCoincidencia
from src.entities.ObjetoEnCustodia import ObjetoEnCustodia
from src.entities.PuntoEntrega import PuntoEntrega


class PosibleCoincidenciaCRUD:
    def __init__(self, db: Session):
        self.db = db

    def crear_coincidencia(
        self,
        objetoEnCustodia_id: UUID,
        reportePerdida_id: UUID,
        usuario_id: UUID,
        score: int,
        notificado: bool = False,
    ) -> PosibleCoincidencia:
        nueva_coincidencia = PosibleCoincidencia(
            objetoEnCustodia_id=objetoEnCustodia_id,
            reportePerdida_id=reportePerdida_id,
            usuario_id=usuario_id,
            score=score,
            notificado=notificado,
        )
        self.db.add(nueva_coincidencia)
        self.db.commit()
        self.db.refresh(nueva_coincidencia)
        return nueva_coincidencia

    def obtener_coincidencia_de_sede_o_404(
        self, posibleCoincidencia_id: UUID, sede_id: UUID
    ) -> PosibleCoincidencia:
        coincidencia = (
            self.db.query(PosibleCoincidencia)
            .join(
                ObjetoEnCustodia,
                PosibleCoincidencia.objetoEnCustodia_id
                == ObjetoEnCustodia.objetoEnCustodia_id,
            )
            .join(
                PuntoEntrega,
                ObjetoEnCustodia.lugar_origen_id == PuntoEntrega.puntoEntrega_id,
            )
            .filter(
                PosibleCoincidencia.posibleCoincidencia_id == posibleCoincidencia_id,
                PuntoEntrega.sede_id == sede_id,
            )
            .first()
        )
        if not coincidencia:
            raise ValueError("Coincidencia no encontrada o no pertenece a tu sede.")
        return coincidencia

    def obtener_coincidencias_por_usuario(
        self, usuario_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[PosibleCoincidencia]:
        return (
            self.db.query(PosibleCoincidencia)
            .filter(PosibleCoincidencia.usuario_id == usuario_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def actualizar_coincidencia(
        self, posibleCoincidencia_id: UUID, **kwargs
    ) -> Optional[PosibleCoincidencia]:
        coincidencia = (
            self.db.query(PosibleCoincidencia)
            .filter(
                PosibleCoincidencia.posibleCoincidencia_id == posibleCoincidencia_id
            )
            .first()
        )
        if not coincidencia:
            return None
        for key, value in kwargs.items():
            if hasattr(coincidencia, key) and value is not None:
                setattr(coincidencia, key, value)
        self.db.commit()
        self.db.refresh(coincidencia)
        return coincidencia
