from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from src.entities.CodigoVerificacion import CodigoVerificacion


class CodigoVerificacionCRUD:
    """
    CRUD de la entidad CodigoVerificacion (OTP de registro y recuperación).
    """

    def __init__(self, db: Session):
        """
        Inicializa el CRUD con una sesión de base de datos.

        Args:
            db (Session): Sesión de SQLAlchemy.
        """
        self.db = db

    def crear_codigo_verificacion(
        self,
        usuario_id: UUID,
        codigo: str,
        tipo: str,
        minutos_expiracion: int = 15,
    ) -> CodigoVerificacion:
        """
        Crea un nuevo código OTP, invalidando los códigos previos del
        mismo tipo que aún estuvieran pendientes para ese usuario.
        """
        if not usuario_id:
            raise ValueError("El usuario es obligatorio")
        if not codigo:
            raise ValueError("El código es obligatorio")
        if not tipo:
            raise ValueError("El tipo de código es obligatorio")

        self._invalidar_codigos_previos(usuario_id, tipo)

        nuevo_codigo = CodigoVerificacion(
            usuario_id=usuario_id,
            codigo=codigo,
            tipo=tipo,
            expira_en=datetime.utcnow() + timedelta(minutes=minutos_expiracion),
            usado=False,
        )

        self.db.add(nuevo_codigo)
        self.db.commit()
        self.db.refresh(nuevo_codigo)

        return nuevo_codigo

    def _invalidar_codigos_previos(self, usuario_id: UUID, tipo: str) -> None:
        """
        Marca como usados todos los códigos no consumidos del mismo tipo
        para un usuario determinado.
        """
        codigos_previos = (
            self.db.query(CodigoVerificacion)
            .filter(
                CodigoVerificacion.usuario_id == usuario_id,
                CodigoVerificacion.tipo == tipo,
                CodigoVerificacion.usado.is_(False),
            )
            .all()
        )
        for codigo in codigos_previos:
            codigo.usado = True
        if codigos_previos:
            self.db.commit()

    def obtener_codigo_verificacion_por_id(
        self, codigoVerificacion_id: UUID
    ) -> Optional[CodigoVerificacion]:
        """
        Obtiene un registro de código de verificación por su ID.
        """
        return (
            self.db.query(CodigoVerificacion)
            .filter(CodigoVerificacion.codigoVerificacion_id == codigoVerificacion_id)
            .first()
        )

    def obtener_codigos_verificacion(
        self, skip: int = 0, limit: int = 100
    ) -> List[CodigoVerificacion]:
        """
        Obtiene el listado general de códigos (para fines de auditoría o soporte).
        """
        return (
            self.db.query(CodigoVerificacion)
            .order_by(CodigoVerificacion.expira_en.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_codigos_verificacion_por_usuario(
        self, usuario_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[CodigoVerificacion]:
        """
        Obtiene el historial de códigos generados para un usuario específico.
        """
        return (
            self.db.query(CodigoVerificacion)
            .filter(CodigoVerificacion.usuario_id == usuario_id)
            .order_by(CodigoVerificacion.expira_en.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_codigos_verificacion_por_tipo(
        self, tipo: str, skip: int = 0, limit: int = 100
    ) -> List[CodigoVerificacion]:
        """
        Obtiene los códigos generados filtrando por su tipo (ej. Registro, Recuperación).
        """
        return (
            self.db.query(CodigoVerificacion)
            .filter(CodigoVerificacion.tipo == tipo)
            .order_by(CodigoVerificacion.expira_en.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_codigos_verificacion_por_usado(
        self, usado: bool, skip: int = 0, limit: int = 100
    ) -> List[CodigoVerificacion]:
        """
        Obtiene los códigos filtrando por su estado de consumo (usado o pendiente).
        """
        return (
            self.db.query(CodigoVerificacion)
            .filter(CodigoVerificacion.usado == usado)
            .order_by(CodigoVerificacion.expira_en.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_codigos_verificacion_por_rango_expiracion(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CodigoVerificacion]:
        """
        Obtiene los códigos cuyo tiempo de expiración cae dentro de un rango de fechas.
        """
        return (
            self.db.query(CodigoVerificacion)
            .filter(CodigoVerificacion.expira_en.between(fecha_inicio, fecha_fin))
            .order_by(CodigoVerificacion.expira_en.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_ultimo_codigo_vigente(
        self, usuario_id: UUID, tipo: str
    ) -> Optional[CodigoVerificacion]:
        """
        Obtiene el último código no usado generado para un usuario y tipo específico.
        """
        return (
            self.db.query(CodigoVerificacion)
            .filter(
                CodigoVerificacion.usuario_id == usuario_id,
                CodigoVerificacion.tipo == tipo,
                CodigoVerificacion.usado.is_(False),
            )
            .order_by(CodigoVerificacion.expira_en.desc())
            .first()
        )

    def validar_codigo_verificacion(
        self, usuario_id: UUID, codigo: str, tipo: str
    ) -> bool:
        """
        Valida el código ingresado por el usuario.

        Si coincide con el último emitido, no está usado y no ha expirado,
        lo marca como usado y retorna `True`. En caso contrario, retorna `False`.
        """
        registro = self.obtener_ultimo_codigo_vigente(usuario_id, tipo)

        if not registro or registro.codigo != codigo:
            return False

        if not registro.esta_vigente():
            return False

        registro.marcar_usado()
        self.db.commit()

        return True

    def marcar_codigo_usado(
        self, codigoVerificacion_id: UUID
    ) -> Optional[CodigoVerificacion]:
        """
        Fuerza la marca de consumo (`usado=True`) para un código por su ID.
        """
        registro = self.obtener_codigo_verificacion_por_id(codigoVerificacion_id)
        if not registro:
            return None

        registro.marcar_usado()
        self.db.commit()
        self.db.refresh(registro)

        return registro

    def eliminar_codigo_verificacion(self, codigoVerificacion_id: UUID) -> bool:
        """
        Realiza un borrado físico del código en base de datos.

        Útil únicamente para tareas de limpieza/purga de códigos vencidos. (no se usa en el flujo normal de negocio).
        """
        registro = self.obtener_codigo_verificacion_por_id(codigoVerificacion_id)
        if not registro:
            return False

        self.db.delete(registro)
        self.db.commit()

        return True
