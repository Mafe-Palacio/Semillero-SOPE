from uuid import UUID
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from src.entities.PosibleCoincidencia import PosibleCoincidencia
from src.entities.ObjetoEnCustodia import ObjetoEnCustodia
from src.entities.PuntoEntrega import PuntoEntrega
from src.entities.Ubicacion import Ubicacion

# Umbral mínimo de score para registrar y notificar una coincidencia.
SCORE_MINIMO_NOTIFICACION = 50


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

    def existe_coincidencia_para_par(
        self, objetoEnCustodia_id: UUID, reportePerdida_id: UUID
    ) -> bool:
        """Evita crear una coincidencia duplicada para el mismo par objeto/reporte."""
        return (
            self.db.query(PosibleCoincidencia)
            .filter(
                PosibleCoincidencia.objetoEnCustodia_id == objetoEnCustodia_id,
                PosibleCoincidencia.reportePerdida_id == reportePerdida_id,
            )
            .first()
            is not None
        )

    def _calcular_score(
        self, fecha_ingreso_objeto: date, fecha_perdida_reporte: date
    ) -> int:
        """Categoría y sede ya se validaron como requisito obligatorio antes
        de llamar esto (ver generar_coincidencias_automaticas); aquí solo se
        suma un bono por qué tan cerca están las fechas."""
        dias_diferencia = abs((fecha_ingreso_objeto - fecha_perdida_reporte).days)

        if dias_diferencia <= 7:
            return 100
        if dias_diferencia <= 15:
            return 80
        if dias_diferencia <= 30:
            return 65
        return 50

    def generar_coincidencias_automaticas(
        self,
        reportes_elegibles: List,
        objetos_elegibles: List,
    ) -> List[PosibleCoincidencia]:
        """
        Algoritmo simple de Smart Match (HU25): compara reportes de pérdida
        aprobados contra objetos en custodia disponibles.

        Requisitos obligatorios para siquiera considerar un par:
          - misma categoría
          - misma sede (lugar_perdida -> sede_id  ==  lugar_origen -> sede_id)

        Si ambos se cumplen, el score (50-100) se calcula según qué tan
        cerca están la fecha de ingreso del objeto y la fecha de pérdida
        reportada. Solo se registran (y notifican) los pares con score >=
        SCORE_MINIMO_NOTIFICACION, y nunca se duplica un par ya existente.
        """
        # Precalcula sede_id de cada reporte (vía su Ubicacion) y de cada
        # objeto (vía su PuntoEntrega) para no repetir consultas por par.
        ubicacion_ids = {r.lugar_perdida_id for r in reportes_elegibles}
        ubicaciones = (
            {
                u.ubicacion_id: u.sede_id
                for u in self.db.query(Ubicacion).filter(
                    Ubicacion.ubicacion_id.in_(ubicacion_ids)
                )
            }
            if ubicacion_ids
            else {}
        )

        punto_ids = {o.lugar_origen_id for o in objetos_elegibles}
        puntos = (
            {
                p.puntoEntrega_id: p.sede_id
                for p in self.db.query(PuntoEntrega).filter(
                    PuntoEntrega.puntoEntrega_id.in_(punto_ids)
                )
            }
            if punto_ids
            else {}
        )

        nuevas_coincidencias: List[PosibleCoincidencia] = []

        for objeto in objetos_elegibles:
            sede_objeto = puntos.get(objeto.lugar_origen_id)
            if sede_objeto is None:
                continue

            for reporte in reportes_elegibles:
                if reporte.categoria != objeto.categoria:
                    continue

                sede_reporte = ubicaciones.get(reporte.lugar_perdida_id)
                if sede_reporte is None or sede_reporte != sede_objeto:
                    continue

                if self.existe_coincidencia_para_par(
                    objeto.objetoEnCustodia_id, reporte.reportePerdida_id
                ):
                    continue

                score = self._calcular_score(
                    objeto.fecha_ingreso, reporte.fecha_perdida
                )
                if score < SCORE_MINIMO_NOTIFICACION:
                    continue

                coincidencia = self.crear_coincidencia(
                    objetoEnCustodia_id=objeto.objetoEnCustodia_id,
                    reportePerdida_id=reporte.reportePerdida_id,
                    usuario_id=reporte.usuario_id,
                    score=score,
                    notificado=False,
                )
                nuevas_coincidencias.append(coincidencia)

        return nuevas_coincidencias

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
