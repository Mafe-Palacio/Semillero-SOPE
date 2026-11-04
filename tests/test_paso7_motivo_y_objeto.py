"""Paso 7: motivo de la solicitud de baja y datos del objeto en /reclamos/me."""
from datetime import date

import pytest

from src.entities.Ubicacion import Ubicacion


@pytest.fixture()
def ubicacion(db, sede):
    u = Ubicacion(sede_id=sede.sede_id, nombre="Bloque J", tipo="BLOQUE")
    db.add(u)
    db.commit()
    return u


def _reporte(client, auth, user, ubicacion):
    r = client.post("/reportes-perdida/", headers=auth(user), json={
        "categoria": "LLAVES", "descripcion": "Llaves rojas",
        "lugar_perdida_id": str(ubicacion.ubicacion_id), "fecha_perdida": str(date.today())})
    assert r.status_code == 201, r.text
    return r.json()["reportePerdida_id"]


def test_baja_de_reporte_guarda_motivo_y_lo_ve_el_admin(client, auth, make_user, sede, ubicacion):
    user = make_user()
    admin = make_user(rol="ADMIN", sede_id=sede.sede_id)
    rid = _reporte(client, auth, user, ubicacion)
    r = client.put(f"/reportes-perdida/{rid}/solicitar-eliminacion", headers=auth(user),
                   json={"motivo": "  Ya encontré el objeto  "})
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "ELIMINACION_PENDIENTE"
    assert r.json()["motivo_eliminacion"] == "Ya encontré el objeto"
    pend = client.get("/reportes-perdida/", headers=auth(admin), params={"eliminacion_solicitada": True}).json()
    assert pend[0]["motivo_eliminacion"] == "Ya encontré el objeto"
    # el admin rechaza la baja: el motivo se limpia
    r = client.put(f"/reportes-perdida/{rid}/resolver-eliminacion", headers=auth(admin),
                   json={"aprobar": False, "motivo": "Sigue vigente"})
    assert r.status_code == 200, r.text
    assert r.json()["motivo_eliminacion"] is None


def test_baja_sin_cuerpo_sigue_funcionando(client, auth, make_user, ubicacion):
    user = make_user()
    rid = _reporte(client, auth, user, ubicacion)
    r = client.put(f"/reportes-perdida/{rid}/solicitar-eliminacion", headers=auth(user))
    assert r.status_code == 200 and r.json()["motivo_eliminacion"] is None


def test_baja_con_motivo_demasiado_largo_422(client, auth, make_user, ubicacion):
    user = make_user()
    rid = _reporte(client, auth, user, ubicacion)
    r = client.put(f"/reportes-perdida/{rid}/solicitar-eliminacion", headers=auth(user),
                   json={"motivo": "x" * 501})
    assert r.status_code == 422


def test_baja_de_publicacion_guarda_motivo(client, auth, make_user, punto, db):
    user = make_user()
    ub = Ubicacion(sede_id=punto.sede_id, nombre="Bloque K", tipo="BLOQUE")
    db.add(ub)
    db.commit()
    r = client.post("/publicaciones-encontradas/", headers=auth(user), json={
        "categoria": "LLAVES", "descripcion": "Llavero", "lugar_hallazgo_id": str(ub.ubicacion_id),
        "lugar_entrega_fisica_id": str(punto.puntoEntrega_id), "fecha_hallazgo": str(date.today())})
    pid = r.json()["publicacionEncontrado_id"]
    r = client.put(f"/publicaciones-encontradas/{pid}/solicitar-eliminacion", headers=auth(user),
                   json={"motivo": "Reporte duplicado"})
    assert r.status_code == 200 and r.json()["motivo_eliminacion"] == "Reporte duplicado"


def test_solo_el_autor_puede_pedir_la_baja(client, auth, make_user, ubicacion):
    user, otro = make_user(), make_user()
    rid = _reporte(client, auth, user, ubicacion)
    r = client.put(f"/reportes-perdida/{rid}/solicitar-eliminacion", headers=auth(otro), json={"motivo": "x"})
    assert r.status_code == 403


def test_reclamos_me_incluye_datos_del_objeto_sin_detalles_internos(client, auth, make_user, objeto, db):
    objeto.detalles_internos = "SECRETO interno"
    objeto.imagen_url = "http://x/img.png"
    db.commit()
    user = make_user()
    r = client.post("/reclamos", headers=auth(user), json={
        "objetoEnCustodia_id": str(objeto.objetoEnCustodia_id),
        "usuario_id": str(user.usuario_id), "es_presencial": False})
    assert r.status_code == 201, r.text
    mis = client.get("/reclamos/me", headers=auth(user))
    assert mis.status_code == 200
    item = mis.json()[0]
    assert item["objeto_categoria"] == "LLAVES"
    assert item["objeto_descripcion"] == "Llavero"
    assert item["objeto_imagen_url"] == "http://x/img.png"
    assert "SECRETO" not in mis.text
