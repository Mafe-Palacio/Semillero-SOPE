"""
Texto legible para el módulo de Auditoría del sitio administrativo.

Convierte un registro crudo de `logs_auditoria` (entidad + id + acción + detalle)
en: quién lo hizo, en qué módulo, qué hizo y un resumen en lenguaje natural, p. ej.:

    "El administrador Ana Pérez aprobó el reporte de pérdida «Mochila negra» del usuario Juan Gómez"
"""

from typing import Iterable, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.entities.ActaEntrega import ActaEntrega
from src.entities.ObjetoEnCustodia import ObjetoEnCustodia
from src.entities.PreguntaSeguridad import PreguntaSeguridad
from src.entities.PublicacionEncontrado import PublicacionEncontrado
from src.entities.Reclamos import Reclamo
from src.entities.ReportePerdida import ReportePerdida
from src.entities.Usuario import Usuario

# entidad -> (clase, nombre del PK, módulo del sitio admin, "el reporte de pérdida")
ENTIDADES = {
    "ReportePerdida": (ReportePerdida, "reportePerdida_id", "Objetos perdidos", "el reporte de pérdida"),
    "PublicacionEncontrado": (
        PublicacionEncontrado,
        "publicacionEncontrado_id",
        "Objetos encontrados",
        "la publicación de objeto encontrado",
    ),
    "ObjetoEnCustodia": (ObjetoEnCustodia, "objetoEnCustodia_id", "Objetos en custodia", "el objeto en custodia"),
    "Reclamo": (Reclamo, "reclamo_id", "Reclamos", "el reclamo"),
    "ActaEntrega": (ActaEntrega, "actaEntrega_id", "Actas de entrega", "el acta de entrega"),
    "PreguntaSeguridad": (
        PreguntaSeguridad,
        "preguntaSeguridad_id",
        "Objetos en custodia",
        "la pregunta de seguridad",
    ),
    "Usuario": (Usuario, "usuario_id", "Usuarios", "al usuario"),
}

# módulo -> entidades (para filtrar la auditoría por módulo)
MODULOS: dict[str, list[str]] = {}
for _ent, (_c, _pk, _mod, _t) in ENTIDADES.items():
    MODULOS.setdefault(_mod, []).append(_ent)

VERBOS = {
    "CREAR": "creó",
    "EDITAR": "actualizó",
    "APROBAR": "aprobó",
    "RECHAZAR": "rechazó",
    "ELIMINAR": "eliminó",
    "BLOQUEAR": "bloqueó",
    "DESBLOQUEAR": "desbloqueó",
    "CAMBIO_ESTADO": "cambió el estado de",
}

PREFIJO_ROL = {
    "ADMIN": "El administrador",
    "SUPERADMIN": "El superadministrador",
    "USER": "El usuario",
}


def _corto(texto: Optional[str], n: int = 60) -> str:
    texto = (texto or "").strip()
    return texto if len(texto) <= n else texto[: n - 1] + "…"


def referencia_entidad(db: Session, obj, incluir_texto: bool = True) -> str:
    """Cómo se nombra un registro en el resumen: «descripción» del usuario NOMBRE.

    Con `incluir_texto=False` (lo que se guarda en la bitácora al eliminar) se omite
    el texto libre que escribió el usuario —descripciones, preguntas, nombres de
    reclamantes— y solo queda la categoría y de quién era: la auditoría nunca
    guarda contenido, solo qué pasó y sobre qué.
    """
    nombre_cls = type(obj).__name__
    if nombre_cls == "Usuario":
        return obj.nombre_completo
    partes = []
    if nombre_cls in ("ReportePerdida", "PublicacionEncontrado", "ObjetoEnCustodia"):
        if incluir_texto:
            partes.append(f"«{_corto(obj.descripcion)}»")
        else:
            partes.append(f"de categoría {getattr(obj.categoria, 'value', obj.categoria)}")
    if nombre_cls == "Reclamo" and incluir_texto:
        custodia = db.get(ObjetoEnCustodia, obj.objetoEnCustodia_id)
        if custodia:
            partes.append(f"del objeto «{_corto(custodia.descripcion)}»")
    if nombre_cls == "ActaEntrega" and incluir_texto:
        partes.append(f"entregada a {obj.nombre_reclamante}")
    if nombre_cls == "PreguntaSeguridad" and incluir_texto:
        partes.append(f"«{_corto(obj.pregunta)}»")
    dueno_id = getattr(obj, "usuario_id", None)
    if dueno_id:
        dueno = db.get(Usuario, dueno_id)
        if dueno:
            partes.append(f"del usuario {dueno.nombre_completo}")
    return " ".join(partes)


def enriquecer_logs(db: Session, logs: Iterable) -> list[dict]:
    """Agrega actor, módulo y resumen a cada registro de auditoría."""
    logs = list(logs)

    actor_ids = {l.usuario_id for l in logs}
    actores = {
        u.usuario_id: u
        for u in db.query(Usuario).filter(Usuario.usuario_id.in_(actor_ids)).all()
    } if actor_ids else {}

    # una consulta por tipo de entidad (no una por registro)
    por_tipo: dict[str, set[UUID]] = {}
    for l in logs:
        por_tipo.setdefault(l.entidad, set()).add(l.entidad_id)
    objetos: dict[tuple[str, UUID], object] = {}
    for nombre, ids in por_tipo.items():
        if nombre not in ENTIDADES:
            continue
        cls, pk, _m, _t = ENTIDADES[nombre]
        for o in db.query(cls).filter(getattr(cls, pk).in_(ids)).all():
            objetos[(nombre, getattr(o, pk))] = o

    salida = []
    for l in logs:
        actor = actores.get(l.usuario_id)
        rol = getattr(actor, "rol", None)
        nombre_actor = actor.nombre_completo if actor else "Usuario desconocido"
        prefijo = PREFIJO_ROL.get(rol, "El usuario")
        verbo = VERBOS.get(getattr(l.accion, "value", l.accion), "modificó")

        info = ENTIDADES.get(l.entidad)
        modulo = info[2] if info else l.entidad
        articulo = info[3] if info else f"un registro de {l.entidad}"

        obj = objetos.get((l.entidad, l.entidad_id))
        if obj is not None:
            ref = referencia_entidad(db, obj)
        elif l.detalle and ": " in l.detalle and (
            getattr(l.accion, "value", l.accion) == "ELIMINAR"
        ):
            ref = l.detalle.split(": ", 1)[1]  # el registro ya no existe; usamos lo guardado
        else:
            ref = ""

        resumen = f"{prefijo} {nombre_actor} {verbo} {articulo}"
        if ref:
            resumen += f" {ref}"
        accion_v = getattr(l.accion, "value", l.accion)
        if accion_v in ("CAMBIO_ESTADO", "EDITAR", "APROBAR", "RECHAZAR") and l.detalle:
            resumen += f" ({l.detalle})"

        salida.append(
            {
                "auditLog_id": l.auditLog_id,
                "entidad": l.entidad,
                "entidad_id": l.entidad_id,
                "accion": l.accion,
                "usuario_id": l.usuario_id,
                "detalle": l.detalle,
                "fecha": l.fecha,
                "usuario_nombre": nombre_actor,
                "usuario_rol": rol,
                "modulo": modulo,
                "resumen": resumen,
            }
        )
    return salida
