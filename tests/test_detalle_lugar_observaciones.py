"""Detalle del lugar y observaciones en reportes de pérdida y hallazgos."""
from datetime import date

import pytest

from src.entities.Ubicacion import Ubicacion


@pytest.fixture()
def ubicacion(db, sede):
    u = Ubicacion(sede_id=sede.sede_id, nombre="Bloque L", tipo="BLOQUE")
    db.add(u)
    db.commit()
    return u


def _publicar(client, auth, user, ub, punto, **extra):
    return client.post("/publicaciones-encontradas/", headers=auth(user), json={
        "categoria": "LLAVES", "descripcion": "Llavero",
        "lugar_hallazgo_id": str(ub.ubicacion_id),
        "lugar_entrega_fisica_id": str(punto.puntoEntrega_id),
        "fecha_hallazgo": str(date.today()), **extra})


def test_hallazgo_guarda_detalle_y_observaciones(client, auth, make_user, ubicacion, punto):
    user = make_user()
    r = _publicar(client, auth, user, ubicacion, punto,
                  detalle_lugar="  Salón L503  ", observaciones="Estaba sobre la silla")
    assert r.status_code == 201, r.text
    assert r.json()["detalle_lugar"] == "Salón L503"
    assert r.json()["observaciones"] == "Estaba sobre la silla"


def test_campos_son_opcionales_y_vacios_quedan_en_null(client, auth, make_user, ubicacion, punto):
    user = make_user()
    r = _publicar(client, auth, user, ubicacion, punto, detalle_lugar="   ")
    assert r.status_code == 201, r.text
    assert r.json()["detalle_lugar"] is None and r.json()["observaciones"] is None


def test_limites_de_longitud(client, auth, make_user, ubicacion, punto):
    user = make_user()
    assert _publicar(client, auth, user, ubicacion, punto, detalle_lugar="x" * 201).status_code == 422
    assert _publicar(client, auth, user, ubicacion, punto, observaciones="x" * 501).status_code == 422


def test_reporte_perdida_guarda_detalle_y_observaciones(client, auth, make_user, ubicacion):
    user = make_user()
    r = client.post("/reportes-perdida/", headers=auth(user), json={
        "categoria": "LLAVES", "descripcion": "Llaves rojas",
        "lugar_perdida_id": str(ubicacion.ubicacion_id), "fecha_perdida": str(date.today()),
        "detalle_lugar": "Salón L503", "observaciones": "Tal vez en el pasillo"})
    assert r.status_code == 201, r.text
    assert r.json()["detalle_lugar"] == "Salón L503"
    assert r.json()["observaciones"] == "Tal vez en el pasillo"


def test_al_aprobar_pasan_a_notas_internas_y_no_salen_en_el_catalogo(
        client, auth, make_user, sede, ubicacion, punto):
    user = make_user()
    admin = make_user(rol="ADMIN", sede_id=sede.sede_id)
    pid = _publicar(client, auth, user, ubicacion, punto,
                    detalle_lugar="Salón L503", observaciones="Sobre la silla").json()["publicacionEncontrado_id"]
    r = client.put(f"/publicaciones-encontradas/{pid}/moderacion", headers=auth(admin),
                   json={"estado": "APROBADA"})
    assert r.status_code == 200, r.text
    objetos = client.get("/objetos-custodia/", headers=auth(admin)).json()
    assert any("Salón L503" in (o.get("detalles_internos") or "") for o in objetos)
    catalogo = client.get("/objetos-custodia/catalogo").text
    assert "Salón L503" not in catalogo and "Sobre la silla" not in catalogo
