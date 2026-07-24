from datetime import date, datetime, timedelta
from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from src.entities.ObjetoEnCustodia import ObjetoEnCustodia

DIAS_POR_VENCER = 150  # ~5 meses
DIAS_SIN_DUENO = 180  # ~6 meses


class ObjetoEnCustodiaCRUD:
    """
    CRUD para la gestión de objetos almacenados físicamente en custodia.
    """

    def __init__(self, db: Session):
        """
        Inicializa el CRUD con una sesión de base de datos.

        Args:
            db (Session): Sesión de SQLAlchemy.
        """
        self.db = db

    def registrar_objeto_custodia(
        self,
        admin_id: UUID,
        categoria: str,
        descripcion: str,
        lugar_origen_id: UUID,
        fecha_ingreso: date,
        publicacionEncontrado_id: Optional[UUID] = None,
        imagen_url: Optional[str] = None,
        detalles_internos: Optional[str] = None,
    ) -> ObjetoEnCustodia:
        """
        Registra un objeto en custodia ingresado directamente por la administradora.
        """
        if not admin_id:
            raise ValueError("El administrador que registra el objeto es obligatorio")
        if not categoria:
            raise ValueError("La categoría es obligatoria")
        if not descripcion:
            raise ValueError("La descripción es obligatoria")
        if not lugar_origen_id:
            raise ValueError("El punto de entrega de origen es obligatorio")
        if not fecha_ingreso:
            raise ValueError("La fecha de ingreso es obligatoria")

        objeto = ObjetoEnCustodia(
            admin_id=admin_id,
            categoria=categoria,
            descripcion=descripcion,
            lugar_origen_id=lugar_origen_id,
            fecha_ingreso=fecha_ingreso,
            publicacionEncontrado_id=publicacionEncontrado_id,
            imagen_url=imagen_url,
            detalles_internos=detalles_internos,
            estado="EN_CUSTODIA",
            en_proceso_validacion=False,
        )

        self.db.add(objeto)
        self.db.commit()
        self.db.refresh(objeto)

        return objeto

    def obtener_objeto_custodia_por_id(
        self, objetoEnCustodia_id: UUID
    ) -> Optional[ObjetoEnCustodia]:
        """
        Busca un objeto en custodia por su ID.
        """
        return (
            self.db.query(ObjetoEnCustodia)
            .filter(ObjetoEnCustodia.objetoEnCustodia_id == objetoEnCustodia_id)
            .first()
        )

    def obtener_objetos_custodia(
        self, skip: int = 0, limit: int = 100
    ) -> List[ObjetoEnCustodia]:
        """
        Obtiene la lista general de objetos en custodia.
        """
        return (
            self.db.query(ObjetoEnCustodia)
            .order_by(ObjetoEnCustodia.fecha_ingreso.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_objeto_custodia_por_publicacion(
        self, publicacionEncontrado_id: UUID
    ) -> Optional[ObjetoEnCustodia]:
        """
        Obtiene el objeto en custodia asociado a una publicación de encontrado.
        """
        return (
            self.db.query(ObjetoEnCustodia)
            .filter(
                ObjetoEnCustodia.publicacionEncontrado_id == publicacionEncontrado_id
            )
            .first()
        )

    def obtener_objetos_custodia_por_estado(
        self, estado: str, skip: int = 0, limit: int = 100
    ) -> List[ObjetoEnCustodia]:
        """
        Filtra objetos en custodia según su estado actual.
        """
        return (
            self.db.query(ObjetoEnCustodia)
            .filter(ObjetoEnCustodia.estado == estado)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_objetos_custodia_disponibles(
        self, skip: int = 0, limit: int = 100
    ) -> List[ObjetoEnCustodia]:
        """
        Lista los objetos en custodia sin bloqueos por reclamación.
        """
        return (
            self.db.query(ObjetoEnCustodia)
            .filter(
                ObjetoEnCustodia.estado == "EN_CUSTODIA",
                ObjetoEnCustodia.en_proceso_validacion.is_(False),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_objetos_custodia_por_punto_entrega(
        self, puntoEntrega_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ObjetoEnCustodia]:
        """
        Obtiene objetos resguardados en un punto de entrega específico.
        """
        return (
            self.db.query(ObjetoEnCustodia)
            .filter(ObjetoEnCustodia.lugar_origen_id == puntoEntrega_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_objetos_custodia_por_categoria(
        self, categoria: str, skip: int = 0, limit: int = 100
    ) -> List[ObjetoEnCustodia]:
        """
        Filtra objetos en custodia por su categoría.
        """
        return (
            self.db.query(ObjetoEnCustodia)
            .filter(ObjetoEnCustodia.categoria == categoria)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_objetos_custodia_por_rango_ingreso(
        self, fecha_inicio: date, fecha_fin: date, skip: int = 0, limit: int = 100
    ) -> List[ObjetoEnCustodia]:
        """
        Obtiene objetos ingresados dentro de un rango de fechas.
        """
        return (
            self.db.query(ObjetoEnCustodia)
            .filter(ObjetoEnCustodia.fecha_ingreso.between(fecha_inicio, fecha_fin))
            .order_by(ObjetoEnCustodia.fecha_ingreso.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_objetos_custodia_por_rango_edicion(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ObjetoEnCustodia]:
        """
        Obtiene objetos modificados dentro de un rango de fecha/hora.
        """
        return (
            self.db.query(ObjetoEnCustodia)
            .filter(ObjetoEnCustodia.fecha_edicion.between(fecha_inicio, fecha_fin))
            .order_by(ObjetoEnCustodia.fecha_edicion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_objetos_custodia_por_en_proceso_validacion(
        self, en_proceso_validacion: bool, skip: int = 0, limit: int = 100
    ) -> List[ObjetoEnCustodia]:
        """
        Filtra objetos según si tienen una validación activa o no.
        """
        return (
            self.db.query(ObjetoEnCustodia)
            .filter(ObjetoEnCustodia.en_proceso_validacion == en_proceso_validacion)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def editar_objeto_custodia(
        self,
        objetoEnCustodia_id: UUID,
        usuario_edita_id: Optional[UUID] = None,
        **kwargs,
    ) -> Optional[ObjetoEnCustodia]:
        """
        Corrige descripción, categoría, imagen o detalles internos ya registrados.
        """
        objeto = self.obtener_objeto_custodia_por_id(objetoEnCustodia_id)
        if not objeto:
            return None

        if usuario_edita_id is None:
            raise ValueError("El usuario autenticado es obligatorio")

        campos_permitidos = {
            "categoria",
            "descripcion",
            "imagen_url",
            "detalles_internos",
        }
        for key, value in kwargs.items():
            if key in campos_permitidos and value is not None:
                setattr(objeto, key, value)

        objeto.usuario_edita_id = usuario_edita_id

        self.db.commit()
        self.db.refresh(objeto)

        return objeto

    def bloquear_objeto_para_validacion(
        self, objetoEnCustodia_id: UUID
    ) -> Optional[ObjetoEnCustodia]:
        """
        Bloquea el objeto mientras se evalúa un reclamo activo.
        """
        objeto = self.obtener_objeto_custodia_por_id(objetoEnCustodia_id)
        if not objeto:
            return None

        objeto.bloquear_para_validacion()

        self.db.commit()
        self.db.refresh(objeto)

        return objeto

    def liberar_objeto_validacion(
        self, objetoEnCustodia_id: UUID
    ) -> Optional[ObjetoEnCustodia]:
        """
        Libera el bloqueo de validación de un objeto.
        """
        objeto = self.obtener_objeto_custodia_por_id(objetoEnCustodia_id)
        if not objeto:
            return None

        objeto.liberar_validacion()

        self.db.commit()
        self.db.refresh(objeto)

        return objeto

    def marcar_objeto_reclamado(
        self, objetoEnCustodia_id: UUID
    ) -> Optional[ObjetoEnCustodia]:
        """
        Marca un objeto como devuelto/reclamado con éxito.
        """
        objeto = self.obtener_objeto_custodia_por_id(objetoEnCustodia_id)
        if not objeto:
            return None

        objeto.estado = "RECLAMADO"
        objeto.en_proceso_validacion = False

        self.db.commit()
        self.db.refresh(objeto)

        return objeto

    def ejecutar_expiracion_y_archivado(self) -> dict:
        """
        Actualiza a POR_VENCER objetos de ~5 meses e identifica candidatos a archivar (~6 meses).
        """
        hoy = date.today()
        limite_por_vencer = hoy - timedelta(days=DIAS_POR_VENCER)
        limite_sin_dueno = hoy - timedelta(days=DIAS_SIN_DUENO)

        candidatos_por_vencer = (
            self.db.query(ObjetoEnCustodia)
            .filter(
                ObjetoEnCustodia.estado == "EN_CUSTODIA",
                ObjetoEnCustodia.fecha_ingreso <= limite_por_vencer,
            )
            .all()
        )
        for objeto in candidatos_por_vencer:
            objeto.estado = "POR_VENCER"
            objeto.fecha_vencimiento_alerta = hoy

        candidatos_archivar = (
            self.db.query(ObjetoEnCustodia)
            .filter(
                ObjetoEnCustodia.estado == "POR_VENCER",
                ObjetoEnCustodia.fecha_ingreso <= limite_sin_dueno,
            )
            .all()
        )

        self.db.commit()

        return {
            "marcados_por_vencer": len(candidatos_por_vencer),
            "candidatos_a_archivar": candidatos_archivar,
        }

    def archivar_objeto_sin_dueno(
        self, objetoEnCustodia_id: UUID
    ) -> Optional[ObjetoEnCustodia]:
        """
        Archiva definitivamente un objeto vencido marcado como sin dueño.
        """
        objeto = self.obtener_objeto_custodia_por_id(objetoEnCustodia_id)
        if not objeto:
            return None

        objeto.estado = "SIN_DUENO_DEFINITIVO"

        self.db.commit()
        self.db.refresh(objeto)

        return objeto