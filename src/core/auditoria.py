"""
Registro automático de auditoría (HU07 CA1, HU10, CU21).

En lugar de llamar manualmente al log en cada endpoint, se engancha al ciclo de
guardado de SQLAlchemy: cada vez que un usuario autenticado crea, edita, modera o
elimina una entidad auditada, se agrega un registro en `logs_auditoria` dentro de la
MISMA transacción (si el cambio falla, tampoco queda el log, y viceversa).

El usuario autor se toma de `get_current_user`, que lo deja en `_actor`.
Nunca se guardan valores sensibles: solo nombres de campos y, para `estado`, el
cambio "antes → después".
"""

from contextvars import ContextVar
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from src.entities.AuditoriaLog import AuditLog
from src.entities.Enums import AccionAuditoria

_actor: ContextVar[Optional[UUID]] = ContextVar("auditoria_actor", default=None)


def set_actor(usuario_id: Optional[UUID]) -> None:
    """Define quién realiza las operaciones de la petición actual."""
    _actor.set(usuario_id)


# Entidades auditadas -> campos que NO cuentan como una edición del usuario
_IGNORAR_COMUN = {"fecha_edicion", "usuario_edita_id", "fecha_creacion"}
AUDITADAS: dict[str, set[str]] = {
    "PublicacionEncontrado": _IGNORAR_COMUN,
    "ReportePerdida": _IGNORAR_COMUN,
    "ObjetoEnCustodia": _IGNORAR_COMUN | {"en_proceso_validacion"},
    "Reclamo": set(),
    "ActaEntrega": set(),
    "PreguntaSeguridad": set(),
    # Usuario: solo cambios de acceso (bloqueo, estado, rol, sede), no el perfil.
    "Usuario": None,  # tratado aparte
}
_USUARIO_CAMPOS = {"is_blocked", "is_active", "rol", "sede_id"}


def _valor(v: Any) -> str:
    return str(getattr(v, "value", v))


def _pk_attr(obj) -> str:
    mapper = inspect(obj).mapper
    return mapper.get_property_by_column(mapper.primary_key[0]).key


def _cambios(obj, ignorar: set[str]) -> dict[str, tuple[Any, Any]]:
    """Campos modificados: {campo: (antes, después)}."""
    out = {}
    for attr in inspect(obj).attrs:
        if attr.key in ignorar or attr.key in _IGNORAR_COMUN:
            continue
        hist = attr.history
        if hist.has_changes() and not hist.added == hist.deleted:
            antes = hist.deleted[0] if hist.deleted else None
            despues = hist.added[0] if hist.added else None
            if _valor(antes) != _valor(despues):
                out[attr.key] = (antes, despues)
    # las colecciones/relaciones no interesan, solo columnas
    cols = {c.key for c in inspect(obj).mapper.column_attrs}
    return {k: v for k, v in out.items() if k in cols}


def _accion_y_detalle(nombre: str, cambios: dict) -> tuple[AccionAuditoria, str]:
    campos = ", ".join(sorted(cambios))
    if nombre == "Usuario":
        if "is_blocked" in cambios:
            if cambios["is_blocked"][1]:
                return AccionAuditoria.BLOQUEAR, "Usuario bloqueado"
            return AccionAuditoria.DESBLOQUEAR, "Usuario desbloqueado"
        return AccionAuditoria.EDITAR, f"Campos: {campos}"
    if "estado" in cambios:
        antes, despues = (_valor(x) for x in cambios["estado"])
        detalle = f"estado: {antes} → {despues}"
        if despues in ("APROBADA", "APROBADO"):
            return AccionAuditoria.APROBAR, detalle
        if despues in ("RECHAZADA", "RECHAZADO"):
            return AccionAuditoria.RECHAZAR, detalle
        return AccionAuditoria.CAMBIO_ESTADO, detalle
    if set(cambios) <= {"eliminacion_solicitada"}:
        return AccionAuditoria.CAMBIO_ESTADO, "Solicitud de eliminación"
    return AccionAuditoria.EDITAR, f"Campos: {campos}"


def _log(obj, accion: AccionAuditoria, detalle: str, actor: UUID) -> AuditLog:
    return AuditLog(
        entidad=type(obj).__name__,
        entidad_id=getattr(obj, _pk_attr(obj)),
        accion=accion,
        usuario_id=actor,
        detalle=detalle[:500],
    )


@event.listens_for(Session, "before_flush")
def _auditar(session: Session, flush_context, instances) -> None:
    actor = _actor.get()
    if actor is None:
        return  # operaciones sin usuario autenticado (registro, tareas internas)

    nuevos = []
    for obj in list(session.new):
        nombre = type(obj).__name__
        if nombre not in AUDITADAS or nombre == "Usuario":
            continue
        pk = _pk_attr(obj)
        if getattr(obj, pk) is None:
            setattr(obj, pk, uuid4())  # el id se asigna ya, para poder registrarlo
        nuevos.append(_log(obj, AccionAuditoria.CREAR, "Registro creado", actor))

    for obj in list(session.dirty):
        nombre = type(obj).__name__
        if nombre not in AUDITADAS or not session.is_modified(obj):
            continue
        if nombre == "Usuario":
            cambios = {
                k: v for k, v in _cambios(obj, set()).items() if k in _USUARIO_CAMPOS
            }
        else:
            cambios = _cambios(obj, AUDITADAS[nombre])
        if not cambios:
            continue
        accion, detalle = _accion_y_detalle(nombre, cambios)
        nuevos.append(_log(obj, accion, detalle, actor))

    for obj in list(session.deleted):
        nombre = type(obj).__name__
        if nombre in AUDITADAS and nombre != "Usuario":
            nuevos.append(_log(obj, AccionAuditoria.ELIMINAR, "Registro eliminado", actor))

    for log in nuevos:
        session.add(log)
