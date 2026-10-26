"""CU08: el catálogo es público (sin token) y no filtra datos sensibles."""
from datetime import date

from src.entities.Ubicacion import Ubicacion
from src.entities.PublicacionEncontrado import PublicacionEncontrado


def test_catalogo_sin_token_200_y_con_nombre_de_lugar(client, objeto, db):
    objeto.detalles_internos = "SERIAL-SECRETO-123"
    db.commit()
    r = client.get("/objetos-custodia/catalogo")
    assert r.status_code == 200, r.text
    item = r.json()[0]
    assert item["lugar_origen_nombre"] == "Oficina OPE"
    assert "SERIAL-SECRETO-123" not in r.text
    assert "detalles_internos" not in item and "admin_id" not in item


def test_catalogo_oculta_reservados_y_archivados(client, objeto, db):
    objeto.en_proceso_validacion = True
    db.commit()
    assert client.get("/objetos-custodia/catalogo").json() == []
    objeto.en_proceso_validacion = False
    objeto.estado = "SIN_DUENO_DEFINITIVO"
    db.commit()
    assert client.get("/objetos-custodia/catalogo").json() == []


def test_buscar_publicaciones_sin_token(client, db, punto, make_user):
    ub = Ubicacion(sede_id=punto.sede_id, nombre="Bloque J", tipo="BLOQUE")
    db.add(ub)
    db.commit()
    u = make_user()
    db.add(PublicacionEncontrado(
        usuario_id=u.usuario_id, categoria="LLAVES", descripcion="Llavero con foto de mi perro",
        lugar_hallazgo_id=ub.ubicacion_id, lugar_entrega_fisica_id=punto.puntoEntrega_id,
        fecha_hallazgo=date.today(), estado="APROBADA"))
    db.add(PublicacionEncontrado(
        usuario_id=u.usuario_id, categoria="LLAVES", descripcion="pendiente",
        lugar_hallazgo_id=ub.ubicacion_id, lugar_entrega_fisica_id=punto.puntoEntrega_id,
        fecha_hallazgo=date.today(), estado="PENDIENTE"))
    db.commit()
    r = client.get(f"/publicaciones-encontradas/buscar?sede_id={punto.sede_id}")
    assert r.status_code == 200, r.text
    assert len(r.json()) == 1  # solo APROBADAS
    assert r.json()[0]["lugar_hallazgo_nombre"] == "Bloque J"
    assert r.json()[0]["lugar_entrega_fisica_nombre"] == "Oficina OPE"
    assert "mi perro" not in r.text  # la descripción libre no se expone


def test_el_resto_sigue_protegido(client, objeto):
    oid = objeto.objetoEnCustodia_id
    for url in ("/objetos-custodia/", f"/objetos-custodia/{oid}", "/publicaciones-encontradas/me",
                "/publicaciones-encontradas/", "/reclamos/me", "/auditoria", "/usuarios/me"):
        assert client.get(url).status_code == 401, url
