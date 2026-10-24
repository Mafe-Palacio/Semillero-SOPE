"""HU25 / CU04: sin celular no se pueden crear reportes, publicaciones ni reclamos."""
from datetime import date


def _reclamo_body(user, objeto):
    return {
        "objetoEnCustodia_id": str(objeto.objetoEnCustodia_id),
        "usuario_id": str(user.usuario_id),
        "es_presencial": False,
    }


def test_reclamo_sin_celular_403(client, auth, make_user, objeto):
    u = make_user(celular=None)
    r = client.post("/reclamos", headers=auth(u), json=_reclamo_body(u, objeto))
    assert r.status_code == 403
    assert "celular" in r.json()["error"]["message"]


def test_celular_en_blanco_tambien_403(client, auth, make_user, objeto):
    u = make_user(celular="   ")
    assert client.post("/reclamos", headers=auth(u), json=_reclamo_body(u, objeto)).status_code == 403


def test_reporte_y_publicacion_sin_celular_403(client, auth, make_user, punto, db):
    from src.entities.Ubicacion import Ubicacion

    ub = Ubicacion(sede_id=punto.sede_id, nombre="Bloque J", tipo="BLOQUE")
    db.add(ub)
    db.commit()
    u = make_user(celular=None)
    rep = client.post("/reportes-perdida/", headers=auth(u), json={
        "categoria": "LLAVES", "descripcion": "x", "lugar_perdida_id": str(ub.ubicacion_id),
        "fecha_perdida": str(date.today())})
    pub = client.post("/publicaciones-encontradas/", headers=auth(u), json={
        "categoria": "LLAVES", "descripcion": "x", "lugar_hallazgo_id": str(ub.ubicacion_id),
        "lugar_entrega_fisica_id": str(punto.puntoEntrega_id), "fecha_hallazgo": str(date.today())})
    assert rep.status_code == 403 and pub.status_code == 403


def test_con_celular_puede_crear(client, auth, make_user, punto, db):
    from src.entities.Ubicacion import Ubicacion

    ub = Ubicacion(sede_id=punto.sede_id, nombre="Bloque J", tipo="BLOQUE")
    db.add(ub)
    db.commit()
    u = make_user(celular="3001112233")
    r = client.post("/reportes-perdida/", headers=auth(u), json={
        "categoria": "LLAVES", "descripcion": "x", "lugar_perdida_id": str(ub.ubicacion_id),
        "fecha_perdida": str(date.today())})
    assert r.status_code == 201, r.text


def test_registrar_celular_desbloquea(client, auth, make_user, objeto):
    u = make_user(celular=None)
    assert client.post("/reclamos", headers=auth(u), json=_reclamo_body(u, objeto)).status_code == 403
    assert client.put("/usuarios/me", headers=auth(u), json={"celular": "3004445566"}).status_code == 200
    assert client.post("/reclamos", headers=auth(u), json=_reclamo_body(u, objeto)).status_code == 201
