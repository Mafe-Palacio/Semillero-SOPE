"""Sitio administrativo: superadmin con sede elegida, resumen de usuarios,
auditoría legible, eliminación por el admin y gestión de administradores."""
from datetime import date

import pytest

from src.entities.AuditoriaLog import AuditLog
from src.entities.ObjetoEnCustodia import ObjetoEnCustodia
from src.entities.PuntoEntrega import PuntoEntrega
from src.entities.Sede import Sede
from src.entities.Ubicacion import Ubicacion


@pytest.fixture()
def ubicacion(db, sede):
    u = Ubicacion(sede_id=sede.sede_id, nombre="Bloque J", tipo="BLOQUE")
    db.add(u)
    db.commit()
    return u


@pytest.fixture()
def otra_sede(db):
    s = Sede(nombre="Robledo", codigo="ROB")
    db.add(s)
    db.commit()
    return s


def _reporte(client, auth, user, ubicacion, descripcion="Mochila negra"):
    r = client.post("/reportes-perdida/", headers=auth(user), json={
        "categoria": "BOLSOS_Y_MALETAS", "descripcion": descripcion,
        "lugar_perdida_id": str(ubicacion.ubicacion_id), "fecha_perdida": str(date.today())})
    assert r.status_code == 201, r.text
    return r.json()["reportePerdida_id"]


def _publicacion(client, auth, user, ubicacion, punto, descripcion="Llavero"):
    r = client.post("/publicaciones-encontradas/", headers=auth(user), json={
        "categoria": "LLAVES", "descripcion": descripcion,
        "lugar_hallazgo_id": str(ubicacion.ubicacion_id),
        "lugar_entrega_fisica_id": str(punto.puntoEntrega_id), "fecha_hallazgo": str(date.today())})
    assert r.status_code == 201, r.text
    return r.json()["publicacionEncontrado_id"]


# ---------------- superadmin elige sede ----------------

def test_superadmin_sin_sede_elegida_recibe_400(client, auth, make_user):
    sa = make_user(rol="SUPERADMIN")
    r = client.get("/reportes-perdida/", headers=auth(sa))
    assert r.status_code == 400 and "X-Sede-Id" in r.json()["error"]["message"]


def test_superadmin_con_sede_elegida_ve_y_modera(client, auth, make_user, sede, ubicacion):
    sa = make_user(rol="SUPERADMIN")
    user = make_user()
    rid = _reporte(client, auth, user, ubicacion)
    h = {**auth(sa), "X-Sede-Id": str(sede.sede_id)}
    lista = client.get("/reportes-perdida/?estado=PENDIENTE", headers=h)
    assert lista.status_code == 200 and len(lista.json()) == 1
    ok = client.put(f"/reportes-perdida/{rid}/moderacion", headers=h, json={"estado": "APROBADA"})
    assert ok.status_code == 200 and ok.json()["estado"] == "APROBADA"


def test_superadmin_en_otra_sede_no_ve_lo_de_la_primera(client, auth, make_user, sede, otra_sede, ubicacion):
    sa = make_user(rol="SUPERADMIN")
    _reporte(client, auth, make_user(), ubicacion)
    h = {**auth(sa), "X-Sede-Id": str(otra_sede.sede_id)}
    assert client.get("/reportes-perdida/", headers=h).json() == []


def test_sede_inexistente_404(client, auth, make_user):
    import uuid
    sa = make_user(rol="SUPERADMIN")
    r = client.get("/reportes-perdida/", headers={**auth(sa), "X-Sede-Id": str(uuid.uuid4())})
    assert r.status_code == 404


def test_admin_no_puede_cambiar_de_sede_con_la_cabecera(client, auth, make_user, sede, otra_sede, ubicacion):
    admin = make_user(rol="ADMIN", sede_id=sede.sede_id)
    _reporte(client, auth, make_user(), ubicacion)
    r = client.get("/reportes-perdida/", headers={**auth(admin), "X-Sede-Id": str(otra_sede.sede_id)})
    assert len(r.json()) == 1  # la cabecera se ignora: sigue viendo SU sede


# ---------------- resumen de usuarios ----------------

def test_resumen_de_usuario_cuenta_actividad(client, auth, make_user, punto, ubicacion):
    admin = make_user(rol="ADMIN", sede_id=punto.sede_id)
    user = make_user()
    _reporte(client, auth, user, ubicacion, "Mochila")
    r2 = _reporte(client, auth, user, ubicacion, "Paraguas")
    _publicacion(client, auth, user, ubicacion, punto)
    client.put(f"/reportes-perdida/{r2}/moderacion", headers=auth(admin), json={"estado": "APROBADA"})

    det = client.get(f"/usuarios/{user.usuario_id}/resumen", headers=auth(admin)).json()
    assert det["reportes_perdida"]["total"] == 2
    assert det["reportes_perdida"]["por_estado"] == {"PENDIENTE": 1, "APROBADA": 1}
    assert det["publicaciones_encontradas"]["total"] == 1
    assert det["reclamos"]["total"] == 0

    lista = client.get("/usuarios/resumen", headers=auth(admin)).json()
    fila = next(x for x in lista if x["usuario_id"] == str(user.usuario_id))
    assert fila["reportes_perdida"]["total"] == 2
    assert all(x["rol"] == "USER" for x in lista)  # los admins no salen en este módulo


def test_resumen_solo_para_admin(client, auth, make_user):
    u = make_user()
    assert client.get("/usuarios/resumen", headers=auth(u)).status_code == 403
    assert client.get(f"/usuarios/{u.usuario_id}/resumen", headers=auth(u)).status_code == 403


# ---------------- auditoría legible ----------------

def test_auditoria_trae_actor_modulo_y_resumen(client, auth, make_user, punto, ubicacion):
    admin = make_user(rol="ADMIN", sede_id=punto.sede_id)
    user = make_user()
    rid = _reporte(client, auth, user, ubicacion, "Mochila negra")
    client.put(f"/reportes-perdida/{rid}/moderacion", headers=auth(admin), json={"estado": "APROBADA"})

    r = client.get("/auditoria", headers=auth(admin))
    assert r.status_code == 200
    aprob = next(x for x in r.json() if x["accion"] == "APROBAR")
    assert aprob["usuario_nombre"] == admin.nombre_completo
    assert aprob["usuario_rol"] == "ADMIN"
    assert aprob["modulo"] == "Objetos perdidos"
    assert aprob["resumen"] == (
        f"El administrador {admin.nombre_completo} aprobó el reporte de pérdida "
        f"«Mochila negra» del usuario {user.nombre_completo} (estado: PENDIENTE → APROBADA)"
    )


def test_auditoria_filtros_modulo_y_rol(client, auth, make_user, punto, ubicacion):
    admin = make_user(rol="ADMIN", sede_id=punto.sede_id)
    user = make_user()
    _reporte(client, auth, user, ubicacion)
    _publicacion(client, auth, user, ubicacion, punto)
    h = auth(admin)
    perdidos = client.get("/auditoria?modulo=Objetos perdidos", headers=h)
    assert perdidos.headers["X-Total-Count"] == "1"
    assert client.get("/auditoria?rol_actor=USER", headers=h).headers["X-Total-Count"] == "2"
    assert client.get("/auditoria?rol_actor=ADMIN", headers=h).headers["X-Total-Count"] == "0"
    assert client.get(f"/auditoria?usuario_id={user.usuario_id}", headers=h).headers["X-Total-Count"] == "2"
    assert client.get("/auditoria?modulo=Inventado", headers=h).status_code == 400


# ---------------- el admin elimina publicaciones ----------------

def test_admin_elimina_reporte_y_queda_auditado_sin_contenido(client, auth, make_user, punto, ubicacion, db):
    admin = make_user(rol="ADMIN", sede_id=punto.sede_id)
    user = make_user()
    rid = _reporte(client, auth, user, ubicacion, "Documento secreto 123")
    r = client.delete(f"/reportes-perdida/{rid}", headers=auth(admin))
    assert r.status_code == 200 and r.json()["exito"] is True
    assert client.get(f"/reportes-perdida/{rid}", headers=auth(admin)).status_code == 404

    db.expire_all()
    log = db.query(AuditLog).filter(AuditLog.accion == "ELIMINAR").one()
    assert log.usuario_id == admin.usuario_id
    assert "secreto" not in log.detalle  # la bitácora no guarda lo que escribió el usuario
    resumen = client.get("/auditoria", headers=auth(admin)).json()[0]["resumen"]
    assert resumen.startswith(f"El administrador {admin.nombre_completo} eliminó el reporte de pérdida")
    assert user.nombre_completo in resumen


def test_admin_elimina_publicacion_encontrada(client, auth, make_user, punto, ubicacion):
    admin = make_user(rol="ADMIN", sede_id=punto.sede_id)
    pid = _publicacion(client, auth, make_user(), ubicacion, punto)
    assert client.delete(f"/publicaciones-encontradas/{pid}", headers=auth(admin)).status_code == 200
    assert client.delete(f"/publicaciones-encontradas/{pid}", headers=auth(admin)).status_code == 404


def test_no_se_elimina_si_ya_tiene_objeto_en_custodia(client, auth, make_user, punto, ubicacion, db):
    admin = make_user(rol="ADMIN", sede_id=punto.sede_id)
    from uuid import UUID

    pid = _publicacion(client, auth, make_user(), ubicacion, punto)
    db.add(ObjetoEnCustodia(admin_id=admin.usuario_id, publicacionEncontrado_id=UUID(pid), categoria="LLAVES",
                            descripcion="Llavero", lugar_origen_id=punto.puntoEntrega_id,
                            fecha_ingreso=date.today()))
    db.commit()
    assert client.delete(f"/publicaciones-encontradas/{pid}", headers=auth(admin)).status_code == 409


def test_eliminar_exige_admin_de_la_misma_sede(client, auth, make_user, punto, ubicacion, otra_sede):
    user = make_user()
    rid = _reporte(client, auth, user, ubicacion)
    assert client.delete(f"/reportes-perdida/{rid}", headers=auth(user)).status_code == 403
    ajeno = make_user(rol="ADMIN", sede_id=otra_sede.sede_id)
    assert client.delete(f"/reportes-perdida/{rid}", headers=auth(ajeno)).status_code == 403


# ---------------- gestión de administradores (superadmin) ----------------

NUEVO_ADMIN = {
    "nombre_completo": "Ana Admin", "cedula": "9001", "correo": "ana.admin@itm.edu.co",
    "password_temporal": "Cambiar123*", "tipo_vinculacion": "ADMINISTRATIVO",
}


def test_superadmin_crea_lista_y_asigna_sede(client, auth, make_user, sede, db):
    sa = make_user(rol="SUPERADMIN")
    r = client.post("/usuarios/administradores", headers=auth(sa), json=NUEVO_ADMIN)
    assert r.status_code == 201, r.text
    admin = r.json()
    assert admin["rol"] == "ADMIN" and admin["is_verified"] and admin["sede_id"] is None

    asignado = client.put(f"/usuarios/{admin['usuario_id']}/moderacion", headers=auth(sa),
                          json={"sede_id": str(sede.sede_id)})
    assert asignado.status_code == 200 and asignado.json()["sede_id"] == str(sede.sede_id)

    lista = client.get(f"/usuarios/administradores?sede_id={sede.sede_id}", headers=auth(sa)).json()
    assert [a["correo"] for a in lista] == ["ana.admin@itm.edu.co"]

    db.expire_all()
    detalles = [l.detalle for l in db.query(AuditLog).all()]
    assert "Administrador creado" in detalles and "Sede asignada" in detalles


def test_solo_superadmin_gestiona_admins(client, auth, make_user, sede):
    admin = make_user(rol="ADMIN", sede_id=sede.sede_id)
    otro = make_user(rol="ADMIN", sede_id=sede.sede_id)
    h = auth(admin)
    assert client.post("/usuarios/administradores", headers=h, json=NUEVO_ADMIN).status_code == 403
    assert client.get("/usuarios/administradores", headers=h).status_code == 403
    uid = otro.usuario_id
    assert client.delete(f"/usuarios/{uid}", headers=h).status_code == 403
    assert client.put(f"/usuarios/{uid}", headers=h, json={"celular": "3000000000"}).status_code == 403
    assert client.post(f"/usuarios/{uid}/reactivar", headers=h).status_code == 403
    assert client.put(f"/usuarios/{uid}/moderacion", headers=h,
                      json={"is_blocked": True, "motivo_bloqueo": "x"}).status_code == 403


def test_superadmin_edita_bloquea_y_desactiva_admin(client, auth, make_user, sede):
    sa = make_user(rol="SUPERADMIN")
    admin = make_user(rol="ADMIN", sede_id=sede.sede_id)
    h, uid = auth(sa), admin.usuario_id
    assert client.put(f"/usuarios/{uid}", headers=h, json={"celular": "3111111111"}).status_code == 200
    assert client.put(f"/usuarios/{uid}/moderacion", headers=h,
                      json={"is_blocked": True, "motivo_bloqueo": "Prueba"}).json()["is_blocked"] is True
    assert client.delete(f"/usuarios/{uid}", headers=h).status_code == 200
    assert client.post(f"/usuarios/{uid}/reactivar", headers=h).json()["is_active"] is True


def test_no_te_puedes_desactivar_ni_bloquear_a_ti_mismo(client, auth, make_user):
    sa = make_user(rol="SUPERADMIN")
    assert client.delete(f"/usuarios/{sa.usuario_id}", headers=auth(sa)).status_code == 400
    assert client.put(f"/usuarios/{sa.usuario_id}/moderacion", headers=auth(sa),
                      json={"is_blocked": True, "motivo_bloqueo": "x"}).status_code == 400


def test_admin_nuevo_valida_correo_clave_y_duplicados(client, auth, make_user):
    sa = make_user(rol="SUPERADMIN")
    h = auth(sa)
    assert client.post("/usuarios/administradores", headers=h,
                       json={**NUEVO_ADMIN, "correo": "ana@gmail.com"}).status_code == 422
    assert client.post("/usuarios/administradores", headers=h,
                       json={**NUEVO_ADMIN, "password_temporal": "123"}).status_code == 422
    assert client.post("/usuarios/administradores", headers=h, json=NUEVO_ADMIN).status_code == 201
    assert client.post("/usuarios/administradores", headers=h, json=NUEVO_ADMIN).status_code == 400
