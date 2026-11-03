"""Un reporte de pérdida aprobado se ve en el listado público; uno pendiente no."""
from datetime import date

import pytest

from src.entities.Ubicacion import Ubicacion


@pytest.fixture()
def ubicacion(db, sede):
    u = Ubicacion(sede_id=sede.sede_id, nombre="Bloque J", tipo="BLOQUE")
    db.add(u)
    db.commit()
    return u


def test_reporte_aprobado_aparece_en_publicos_sin_datos_del_dueno(client, auth, make_user, sede, ubicacion):
    user = make_user()
    admin = make_user(rol="ADMIN", sede_id=sede.sede_id)
    r = client.post("/reportes-perdida/", headers=auth(user), json={
        "categoria": "LLAVES", "descripcion": "Llaves rojas",
        "lugar_perdida_id": str(ubicacion.ubicacion_id), "fecha_perdida": str(date.today())})
    assert r.status_code == 201, r.text
    rid = r.json()["reportePerdida_id"]

    assert client.get("/reportes-perdida/publicos").json() == []  # pendiente: no se ve

    ok = client.put(f"/reportes-perdida/{rid}/moderacion", headers=auth(admin), json={"estado": "APROBADA"})
    assert ok.status_code == 200, ok.text

    lista = client.get("/reportes-perdida/publicos")  # sin token
    assert lista.status_code == 200
    assert len(lista.json()) == 1
    item = lista.json()[0]
    assert item["descripcion"] == "Llaves rojas" and item["lugar_perdida_nombre"] == "Bloque J"
    assert "usuario_id" not in item and "celular" not in str(item)
