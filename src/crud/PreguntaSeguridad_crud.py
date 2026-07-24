from uuid import UUID
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from src.entities.PreguntaSeguridad import PreguntaSeguridad


class PreguntaSeguridadCRUD:
    """CRUD de la entidad PreguntaSeguridad para validación de objetos."""

    MIN_PREGUNTAS = 1
    MAX_PREGUNTAS = 10  # tope de sanidad; la admin decide cuántas dentro de este rango

    def __init__(self, db: Session):
        """
        Inicializa el CRUD con una sesión de base de datos.

        Args:
            db (Session): Sesión de SQLAlchemy.
        """
        self.db = db

    def crear_preguntas_seguridad(
        self,
        objetoEnCustodia_id: UUID,
        preguntas: List[Dict[str, str]],
    ) -> List[PreguntaSeguridad]:
        """
        Crea la cantidad de preguntas de seguridad que la administradora
        defina para el objeto (HU04).
        preguntas: lista de dicts {"pregunta": str, "respuesta_correcta": str}
        """
        if not objetoEnCustodia_id:
            raise ValueError("El objeto en custodia es obligatorio")
        if not (self.MIN_PREGUNTAS <= len(preguntas) <= self.MAX_PREGUNTAS):
            raise ValueError(
                f"Se debe configurar entre {self.MIN_PREGUNTAS} y "
                f"{self.MAX_PREGUNTAS} preguntas por objeto"
            )

        if self.obtener_preguntas_seguridad_por_objeto(objetoEnCustodia_id):
            raise ValueError("Este objeto ya tiene preguntas de seguridad configuradas")

        nuevas_preguntas = []
        for orden, item in enumerate(preguntas, start=1):
            if not item.get("pregunta") or not item.get("respuesta_correcta"):
                raise ValueError("Cada pregunta requiere texto y respuesta correcta")

            nueva = PreguntaSeguridad(
                objetoEnCustodia_id=objetoEnCustodia_id,
                pregunta=item["pregunta"],
                respuesta_correcta=item["respuesta_correcta"],
                orden=orden,
            )
            self.db.add(nueva)
            nuevas_preguntas.append(nueva)

        self.db.commit()
        for pregunta in nuevas_preguntas:
            self.db.refresh(pregunta)

        return nuevas_preguntas

    def obtener_preguntas_seguridad_por_objeto(
        self, objetoEnCustodia_id: UUID, skip: int = 0, limit: int = 10
    ) -> List[PreguntaSeguridad]:
        """
        Obtiene las preguntas de seguridad asociadas a un objeto.
        """
        return (
            self.db.query(PreguntaSeguridad)
            .filter(PreguntaSeguridad.objetoEnCustodia_id == objetoEnCustodia_id)
            .order_by(PreguntaSeguridad.orden)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_pregunta_seguridad_por_id(
        self, preguntaSeguridad_id: UUID
    ) -> Optional[PreguntaSeguridad]:
        """
        Busca una pregunta de seguridad específica por su ID.
        """
        return (
            self.db.query(PreguntaSeguridad)
            .filter(PreguntaSeguridad.preguntaSeguridad_id == preguntaSeguridad_id)
            .first()
        )

    def actualizar_pregunta_seguridad(
        self,
        preguntaSeguridad_id: UUID,
        pregunta: Optional[str] = None,
        respuesta_correcta: Optional[str] = None,
    ) -> Optional[PreguntaSeguridad]:
        """
        Corrige el texto o la respuesta de una pregunta puntual, antes
        de que existan reclamos activos evaluándola.
        """
        registro = self.obtener_pregunta_seguridad_por_id(preguntaSeguridad_id)
        if not registro:
            return None

        if pregunta is not None:
            registro.pregunta = pregunta
        if respuesta_correcta is not None:
            registro.respuesta_correcta = respuesta_correcta

        self.db.commit()
        self.db.refresh(registro)

        return registro

    def validar_respuestas_seguridad(
        self, objetoEnCustodia_id: UUID, respuestas: Dict[UUID, str]
    ) -> bool:
        """
        Valida que TODAS las respuestas del reclamante coincidan con
        las preguntas configuradas para el objeto.
        """
        preguntas = self.obtener_preguntas_seguridad_por_objeto(objetoEnCustodia_id)

        if not preguntas:
            return False
        if len(respuestas) != len(preguntas):
            return False

        for pregunta in preguntas:
            respuesta_usuario = respuestas.get(pregunta.preguntaSeguridad_id)
            if respuesta_usuario is None:
                return False
            if not pregunta.validar_respuesta(respuesta_usuario):
                return False

        return True

    def eliminar_pregunta_seguridad(self, preguntaSeguridad_id: UUID) -> bool:
        """
        Elimina una única pregunta (por su id) en vez de todo el bloque.
        """
        registro = self.obtener_pregunta_seguridad_por_id(preguntaSeguridad_id)
        if not registro:
            return False

        self.db.delete(registro)
        self.db.commit()

        return True

    def eliminar_preguntas_seguridad_de_objeto(self, objetoEnCustodia_id: UUID) -> int:
        """
        Elimina todas las preguntas de seguridad pertenecientes a un objeto.
        """
        preguntas = self.obtener_preguntas_seguridad_por_objeto(
            objetoEnCustodia_id, skip=0, limit=self.MAX_PREGUNTAS
        )
        for pregunta in preguntas:
            self.db.delete(pregunta)
        self.db.commit()
        return len(preguntas)
