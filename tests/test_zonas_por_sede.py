import uuid
from datetime import date

from src.entities.PuntoEntrega import PuntoEntrega
from src.entities.Sede import Sede
from src.entities.Ubicacion import Ubicacion


def _otra_sede(db):
    s = Sede(nombre="Castilla", codigo="CAST")
    db.add(s)
    db.commit()
    p = PuntoEntrega(sede_id=s.sede_id, nombre="Oficina Castilla", tipo="OFICINA")
    u = Ubicacion(nombre="Bloque C", tipo="BLOQUE", sede_id=s.sede_id)
    db.add_all([p, u])
    db.commit()
    return s, p, u


def _ubic(db, sede, nombre="Cafetería"):
    u = Ubicacion(nombre=nombre, tipo="ZONA_COMUN", sede_id=sede.sede_id)
    db.add(u)
    db.commit()
    return u


def _hallazgo(u, p):
    return {
        "categoria": "LLAVES",
        "descripcion": "Llavero con tres llaves",
        "lugar_hallazgo_id": str(u.ubicacion_id),
        "lugar_entrega_fisica_id": str(p.puntoEntrega_id),
        "fecha_hallazgo": date.today().isoformat(),
    }


def test_hallazgo_en_misma_sede_ok(client, auth, make_user, db, sede, punto):
    user = make_user()
    r = client.post("/publicaciones-encontradas/", json=_hallazgo(_ubic(db, sede), punto), headers=auth(user))
    assert r.status_code == 201, r.text


def test_hallazgo_con_punto_de_otra_sede_se_rechaza(client, auth, make_user, db, sede, punto):
    user = make_user()
    _, punto_otra, _ = _otra_sede(db)
    r = client.post("/publicaciones-encontradas/", json=_hallazgo(_ubic(db, sede), punto_otra), headers=auth(user))
    assert r.status_code == 400
    assert "misma sede" in r.text


def test_hallazgo_con_lugar_inexistente(client, auth, make_user, db, punto):
    user = make_user()
    body = {**_hallazgo(type("U", (), {"ubicacion_id": uuid.uuid4()}), punto)}
    r = client.post("/publicaciones-encontradas/", json=body, headers=auth(user))
    assert r.status_code == 400


def test_reporte_perdida_lugar_inexistente(client, auth, make_user):
    user = make_user()
    r = client.post("/reportes-perdida/", json={
        "categoria": "LLAVES", "descripcion": "Llaves perdidas en la mañana",
        "lugar_perdida_id": str(uuid.uuid4()), "fecha_perdida": date.today().isoformat(),
    }, headers=auth(user))
    assert r.status_code == 400
