"""Eliminar preguntas de seguridad: caso normal y pregunta ya respondida en un reclamo."""
from uuid import UUID

from src.entities.Reclamos import Reclamo
from src.entities.RespuestaSeguridad import RespuestaSeguridad


def _crear(client, auth, admin, objeto, n=2):
    oid = str(objeto.objetoEnCustodia_id)
    r = client.post(f"/preguntas-seguridad/objeto/{oid}", headers=auth(admin), json={
        "objetoEnCustodia_id": oid,
        "preguntas": [{"pregunta": f"¿P{i}?", "respuesta_correcta": f"r{i}"} for i in range(n)]})
    assert r.status_code == 201, r.text
    return oid, [p["preguntaSeguridad_id"] for p in r.json()]


def test_elimina_una_pregunta_y_quedan_las_demas(client, auth, make_user, sede, objeto):
    admin = make_user(rol="ADMIN", sede_id=sede.sede_id)
    oid, ids = _crear(client, auth, admin, objeto)
    r = client.delete(f"/preguntas-seguridad/{ids[0]}", headers=auth(admin))
    assert r.status_code == 200, r.text
    quedan = client.get(f"/preguntas-seguridad/objeto/{oid}", headers=auth(admin)).json()
    assert [p["preguntaSeguridad_id"] for p in quedan] == [ids[1]]


def test_pregunta_ya_respondida_da_409_claro_y_no_se_borra(client, auth, make_user, sede, objeto, db):
    admin, user = make_user(rol="ADMIN", sede_id=sede.sede_id), make_user()
    oid, ids = _crear(client, auth, admin, objeto)
    rec = Reclamo(usuario_id=user.usuario_id, objetoEnCustodia_id=objeto.objetoEnCustodia_id,
                  estado="ENVIADO", es_presencial=False)
    db.add(rec)
    db.commit()
    db.add(RespuestaSeguridad(reclamo_id=rec.reclamo_id, preguntaSeguridad_id=UUID(ids[0]), respuesta_usuario="x"))
    db.commit()
    r = client.delete(f"/preguntas-seguridad/{ids[0]}", headers=auth(admin))
    assert r.status_code == 409, r.text
    assert "reclamos que respondieron" in r.json()["error"]["message"]
    r = client.delete(f"/preguntas-seguridad/objeto/{oid}", headers=auth(admin))
    assert r.status_code == 409, r.text
    assert len(client.get(f"/preguntas-seguridad/objeto/{oid}", headers=auth(admin)).json()) == 2
