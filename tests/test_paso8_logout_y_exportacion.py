"""Paso 8: cierre de sesión con revocación (HU35), exportación de auditoría y escape HTML."""
from src.core.auth import create_access_token, create_refresh_token
from src.core.config import get_settings
from src.utils.notifications import NotificationDispatcher


def _tokens(u):
    s = get_settings()
    acc = create_access_token(subject=u.usuario_id, correo=u.correo, rol=u.rol, settings=s)
    ref = create_refresh_token(subject=u.usuario_id, settings=s)
    return acc, ref


def test_logout_revoca_access_y_refresh(client, make_user):
    u = make_user()
    acc, ref = _tokens(u)
    h = {"Authorization": f"Bearer {acc}"}
    assert client.get("/usuarios/me", headers=h).status_code == 200
    assert client.post("/auth/refresh", json={"refresh_token": ref}).status_code == 200

    r = client.post("/auth/logout", headers=h, json={"refresh_token": ref})
    assert r.status_code == 200 and r.json()["exito"] is True

    assert client.get("/usuarios/me", headers=h).status_code == 401
    assert client.post("/auth/refresh", json={"refresh_token": ref}).status_code == 401
    # idempotente: repetirlo no falla
    assert client.post("/auth/logout", headers=h, json={"refresh_token": ref}).status_code == 200


def test_logout_solo_afecta_la_sesion_cerrada(client, make_user):
    u = make_user()
    a1, r1 = _tokens(u)
    import time; time.sleep(1.1)  # iat distinto => otro JWT
    a2, r2 = _tokens(u)
    client.post("/auth/logout", headers={"Authorization": f"Bearer {a1}"}, json={"refresh_token": r1})
    assert client.get("/usuarios/me", headers={"Authorization": f"Bearer {a2}"}).status_code == 200


def test_logout_sin_tokens_validos_no_falla(client):
    assert client.post("/auth/logout", json={"refresh_token": "basura"}).status_code == 200
    assert client.post("/auth/logout").status_code == 200


def test_exportar_auditoria_csv_y_xlsx(client, auth, make_user, sede):
    admin = make_user(rol="ADMIN", sede_id=sede.sede_id)
    user = make_user()
    client.put("/usuarios/me", headers=auth(user), json={"carnet": "123456"})
    r = client.get("/exportaciones/auditoria", headers=auth(admin), params={"formato": "csv"})
    assert r.status_code == 200, r.text
    assert "text/csv" in r.headers["content-type"]
    assert "auditoria_" in r.headers["content-disposition"]
    assert r.content.decode("utf-8-sig").splitlines()[0].startswith("Fecha,M")
    x = client.get("/exportaciones/auditoria", headers=auth(admin), params={"formato": "xlsx", "accion": "EDITAR"})
    assert x.status_code == 200 and x.content[:2] == b"PK"


def test_exportar_auditoria_exige_admin(client, auth, make_user):
    assert client.get("/exportaciones/auditoria", headers=auth(make_user())).status_code == 403


def test_correos_escapan_html_de_usuarios(monkeypatch):
    enviados = []
    d = NotificationDispatcher()
    monkeypatch.setattr(d, "_enviar_correo", lambda dest, asunto, cuerpo, *a, **k: enviados.append(cuerpo) or True)
    d.enviar_cierre_exitoso_reclamante("a@b.co", "<script>alert(1)</script>")
    d.enviar_cambio_estado_reclamo("a@b.co", "RECHAZADO", '<img src=x onerror="x">')
    d.enviar_correo_acta_entrega("a@b.co", "javascript:alert(1)")
    todo = "".join(enviados)
    assert "<script>" not in todo and "<img" not in todo and 'href="javascript' not in todo
    assert "&lt;script&gt;" in todo


def test_bitacora_usa_del_en_vez_de_de_el(client, auth, make_user, sede):
    from datetime import date
    from src.entities.Ubicacion import Ubicacion
    from src.database.config import get_db  # noqa: F401
    admin = make_user(rol="ADMIN", sede_id=sede.sede_id)
    user = make_user()
    db = next(client.app.dependency_overrides[get_db]())
    ub = Ubicacion(sede_id=sede.sede_id, nombre="Bloque J", tipo="BLOQUE"); db.add(ub); db.commit()
    rid = client.post("/reportes-perdida/", headers=auth(user), json={
        "categoria": "LLAVES", "descripcion": "Llaves rojas",
        "lugar_perdida_id": str(ub.ubicacion_id), "fecha_perdida": str(date.today())}).json()["reportePerdida_id"]
    client.put(f"/reportes-perdida/{rid}/solicitar-eliminacion", headers=auth(user), json={"motivo": "ya apareció"})
    res = [r["resumen"] for r in client.get("/auditoria", headers=auth(admin)).json()]
    assert any("cambió el estado del reporte" in r for r in res), res
    assert not any(" de el " in r for r in res)
