from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from src.entities.PosibleCoincidencia import PosibleCoincidencia


class PosibleCoincidenciaCRUD:
    """CRUD para gestionar los registros del Smart Match."""

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
        """Crea un nuevo registro de coincidencia en la base de datos."""
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

    def obtener_coincidencia_por_id(
        self, posibleCoincidencia_id: UUID
    ) -> Optional[PosibleCoincidencia]:
        """Busca una coincidencia puntual por su ID."""
        return (
            self.db.query(PosibleCoincidencia)
            .filter(
                PosibleCoincidencia.posibleCoincidencia_id == posibleCoincidencia_id
            )
            .first()
        )

    def obtener_coincidencias_por_usuario(
        self, usuario_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[PosibleCoincidencia]:
        """Obtiene todas las posibles coincidencias para un usuario en particular."""
        return (
            self.db.query(PosibleCoincidencia)
            .filter(PosibleCoincidencia.usuario_id == usuario_id)
            .order_by(PosibleCoincidencia.fecha_deteccion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def actualizar_coincidencia(
        self, posibleCoincidencia_id: UUID, **kwargs
    ) -> Optional[PosibleCoincidencia]:
        """Actualiza atributos de la coincidencia (ej. marcar como notificado)."""
        coincidencia = self.obtener_coincidencia_por_id(posibleCoincidencia_id)
        if not coincidencia:
            return None

        for key, value in kwargs.items():
            if hasattr(coincidencia, key) and value is not None:
                setattr(coincidencia, key, value)

        self.db.commit()
        self.db.refresh(coincidencia)
        return coincidencia

    def eliminar_coincidencia(self, posibleCoincidencia_id: UUID) -> bool:
        """Elimina un registro de coincidencia."""
        coincidencia = self.obtener_coincidencia_por_id(posibleCoincidencia_id)
        if not coincidencia:
            return False

        self.db.delete(coincidencia)
        self.db.commit()
        return True
