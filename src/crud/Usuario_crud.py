from datetime import datetime
from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from src.entities.Usuario import Usuario


class UsuarioCRUD:
    """
    CRUD de la entidad Usuario.
    """

    def __init__(self, db: Session):
        """
        Inicializa el CRUD con una sesión de base de datos.

        Args:
            db (Session): Sesión de SQLAlchemy.
        """
        self.db = db

    def crear_usuario(
        self,
        nombre_completo: str,
        cedula: str,
        correo: str,
        hashed_password: str,
        rol: str,
        tipo_vinculacion: str,
    ) -> Usuario:
        """
        Registra un usuario nuevo.
        """
        if not nombre_completo:
            raise ValueError("El nombre completo es obligatorio")
        if not cedula:
            raise ValueError("La cédula es obligatoria")
        if not correo:
            raise ValueError("El correo institucional es obligatorio")
        if not hashed_password:
            raise ValueError("La contraseña es obligatoria")

        if self.obtener_usuario_por_correo(correo):
            raise ValueError(
                f"Ya existe un usuario registrado con el correo '{correo}'"
            )
        if self.obtener_usuario_por_cedula(cedula):
            raise ValueError(
                f"Ya existe un usuario registrado con la cédula '{cedula}'"
            )

        usuario = Usuario(
            nombre_completo=nombre_completo,
            cedula=cedula,
            correo=correo,
            hashed_password=hashed_password,
            rol=rol,
            tipo_vinculacion=tipo_vinculacion,
            is_verified=False,
            is_active=True,
            is_blocked=False,
        )

        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)

        return usuario

    def obtener_usuario_por_id(self, usuario_id: UUID) -> Optional[Usuario]:
        """
        Obtiene un usuario por su identificador único.
        """
        return self.db.query(Usuario).filter(Usuario.usuario_id == usuario_id).first()

    def obtener_usuario_por_correo(self, correo: str) -> Optional[Usuario]:
        """
        Obtiene un usuario por su correo electrónico institucional.
        """
        return self.db.query(Usuario).filter(Usuario.correo == correo).first()

    def obtener_usuario_por_cedula(self, cedula: str) -> Optional[Usuario]:
        """
        Obtiene un usuario por su número de cédula.
        """
        return self.db.query(Usuario).filter(Usuario.cedula == cedula).first()

    def obtener_usuario_por_carnet(self, carnet: str) -> Optional[Usuario]:
        """
        Obtiene un usuario por su número de carné institucional.
        """
        return self.db.query(Usuario).filter(Usuario.carnet == carnet).first()

    def obtener_usuarios_por_celular(
        self, celular: str, skip: int = 0, limit: int = 100
    ) -> List[Usuario]:
        """
        Obtiene los usuarios asociados a un número de celular específico.
        """
        return (
            self.db.query(Usuario)
            .filter(Usuario.celular == celular)
            .order_by(Usuario.nombre_completo)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_usuarios(self, skip: int = 0, limit: int = 100) -> List[Usuario]:
        """
        Obtiene los usuarios asociados a un número de celular específico.
        """
        return (
            self.db.query(Usuario)
            .order_by(Usuario.nombre_completo)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_usuarios_por_nombre(
        self, nombre: str, skip: int = 0, limit: int = 100
    ) -> List[Usuario]:
        """
        Busca usuarios coincidiendo parcialmente con el nombre completo.
        """
        return (
            self.db.query(Usuario)
            .filter(Usuario.nombre_completo.ilike(f"%{nombre}%"))
            .order_by(Usuario.nombre_completo)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_usuarios_por_rol(
        self, rol: str, skip: int = 0, limit: int = 100
    ) -> List[Usuario]:
        """
        Obtiene los usuarios filtrados por su rol en el sistema.
        """
        return (
            self.db.query(Usuario)
            .filter(Usuario.rol == rol)
            .order_by(Usuario.nombre_completo)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_usuarios_por_tipo_vinculacion(
        self, tipo_vinculacion: str, skip: int = 0, limit: int = 100
    ) -> List[Usuario]:
        """
        Obtiene usuarios filtrados por su tipo de vinculación institucional.
        """
        return (
            self.db.query(Usuario)
            .filter(Usuario.tipo_vinculacion == tipo_vinculacion)
            .order_by(Usuario.nombre_completo)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_usuarios_por_sede(
        self, sede_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Usuario]:
        """
        Obtiene los usuarios asociados a una sede específica.
        """
        return (
            self.db.query(Usuario)
            .filter(Usuario.sede_id == sede_id)
            .order_by(Usuario.nombre_completo)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_administradores_por_sede(
        self, sede_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Usuario]:
        """
        Obtiene la lista de administradores asignados a una sede determinada.
        """
        return (
            self.db.query(Usuario)
            .filter(Usuario.sede_id == sede_id, Usuario.rol == "ADMIN")
            .order_by(Usuario.nombre_completo)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_usuarios_por_verificado(
        self, is_verified: bool, skip: int = 0, limit: int = 100
    ) -> List[Usuario]:
        """
        Obtiene usuarios según su estado de verificación de correo.
        """
        return (
            self.db.query(Usuario)
            .filter(Usuario.is_verified == is_verified)
            .order_by(Usuario.nombre_completo)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_usuarios_por_activo(
        self, is_active: bool, skip: int = 0, limit: int = 100
    ) -> List[Usuario]:
        """
        Obtiene usuarios según su estado de activación de cuenta.
        """
        return (
            self.db.query(Usuario)
            .filter(Usuario.is_active == is_active)
            .order_by(Usuario.nombre_completo)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_usuarios_bloqueados(
        self, skip: int = 0, limit: int = 100
    ) -> List[Usuario]:
        """
        Obtiene la lista de usuarios con bloqueo activo en la plataforma.
        """
        return (
            self.db.query(Usuario)
            .filter(Usuario.is_blocked.is_(True))
            .order_by(Usuario.nombre_completo)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_usuarios_por_rango_creacion(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Usuario]:
        """
        Obtiene usuarios registrados dentro de un rango de fechas.
        """
        return (
            self.db.query(Usuario)
            .filter(Usuario.fecha_creacion.between(fecha_inicio, fecha_fin))
            .order_by(Usuario.fecha_creacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_usuarios_por_rango_edicion(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Usuario]:
        """
        Obtiene usuarios modificados dentro de un rango de fechas.
        """
        return (
            self.db.query(Usuario)
            .filter(Usuario.fecha_edicion.between(fecha_inicio, fecha_fin))
            .order_by(Usuario.fecha_edicion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def verificar_usuario(self, usuario_id: UUID) -> Optional[Usuario]:
        """
        Marca el usuario como verificado tras validar el código OTP.
        """
        usuario = self.obtener_usuario_por_id(usuario_id)
        if not usuario:
            return None

        usuario.is_verified = True

        self.db.commit()
        self.db.refresh(usuario)

        return usuario

    def actualizar_perfil_usuario(
        self,
        usuario_id: UUID,
        celular: Optional[str] = None,
        carnet: Optional[str] = None,
    ) -> Optional[Usuario]:
        """
        Actualiza los campos editables directamente por el usuario desde su perfil (HU23).
        """
        usuario = self.obtener_usuario_por_id(usuario_id)
        if not usuario:
            return None

        if celular is not None:
            usuario.celular = celular
        if carnet is not None:
            usuario.carnet = carnet

        usuario.usuario_edita_id = usuario_id

        self.db.commit()
        self.db.refresh(usuario)

        return usuario

    def actualizar_usuario(
        self, usuario_id: UUID, usuario_edita_id: UUID, **kwargs
    ) -> Optional[Usuario]:
        """Actualización administrativa genérica de un usuario (nombre_completo,
        celular, carnet, tipo_vinculacion). No toca campos sensibles."""
        usuario = self.obtener_usuario_por_id(usuario_id)
        if not usuario:
            return None

        if usuario_edita_id is None:
            raise ValueError("El usuario autenticado es obligatorio")

        campos_permitidos = {
            "nombre_completo",
            "celular",
            "carnet",
            "tipo_vinculacion",
        }
        for key, value in kwargs.items():
            if key in campos_permitidos and value is not None:
                setattr(usuario, key, value)

        usuario.usuario_edita_id = usuario_edita_id

        self.db.commit()
        self.db.refresh(usuario)

        return usuario

    def cambiar_password_usuario(
        self, usuario_id: UUID, hashed_password: str
    ) -> Optional[Usuario]:
        """
        Actualiza la contraseña hasheada del usuario.
        """
        usuario = self.obtener_usuario_por_id(usuario_id)
        if not usuario:
            return None

        usuario.hashed_password = hashed_password

        self.db.commit()
        self.db.refresh(usuario)

        return usuario

    def bloquear_usuario(
        self, usuario_id: UUID, motivo_bloqueo: str, usuario_edita_id: UUID
    ) -> Optional[Usuario]:
        """
        Bloquea el acceso de un usuario.
        """
        if not motivo_bloqueo:
            raise ValueError("El motivo de bloqueo es obligatorio")

        usuario = self.obtener_usuario_por_id(usuario_id)
        if not usuario:
            return None

        usuario.is_blocked = True
        usuario.motivo_bloqueo = motivo_bloqueo
        usuario.usuario_edita_id = usuario_edita_id

        self.db.commit()
        self.db.refresh(usuario)

        return usuario

    def desbloquear_usuario(
        self, usuario_id: UUID, usuario_edita_id: UUID
    ) -> Optional[Usuario]:
        """
        Remueve el bloqueo de acceso de un usuario.
        """
        usuario = self.obtener_usuario_por_id(usuario_id)
        if not usuario:
            return None

        usuario.is_blocked = False
        usuario.motivo_bloqueo = None
        usuario.usuario_edita_id = usuario_edita_id

        self.db.commit()
        self.db.refresh(usuario)

        return usuario

    def desactivar_usuario(
        self, usuario_id: UUID, usuario_edita_id: UUID
    ) -> Optional[Usuario]:
        """Desactiva la cuenta (is_active=False) sin borrar el historial asociado."""
        usuario = self.obtener_usuario_por_id(usuario_id)
        if not usuario:
            return None

        usuario.is_active = False
        usuario.usuario_edita_id = usuario_edita_id

        self.db.commit()
        self.db.refresh(usuario)

        return usuario

    def reactivar_usuario(
        self, usuario_id: UUID, usuario_edita_id: UUID
    ) -> Optional[Usuario]:
        """
        Reactiva la cuenta de un usuario previamente desactivado.
        """
        usuario = self.obtener_usuario_por_id(usuario_id)
        if not usuario:
            return None

        usuario.is_active = True
        usuario.usuario_edita_id = usuario_edita_id

        self.db.commit()
        self.db.refresh(usuario)

        return usuario

    def asignar_sede_admin(
        self, usuario_id: UUID, sede_id: UUID, usuario_edita_id: UUID
    ) -> Optional[Usuario]:
        """
        Asigna la sede que administrará un usuario con rol ADMIN.
        """
        usuario = self.obtener_usuario_por_id(usuario_id)
        if not usuario:
            return None

        if usuario.rol != "ADMIN":
            raise ValueError("Solo se puede asignar sede a usuarios con rol ADMIN")

        usuario.sede_id = sede_id
        usuario.usuario_edita_id = usuario_edita_id

        self.db.commit()
        self.db.refresh(usuario)

        return usuario
