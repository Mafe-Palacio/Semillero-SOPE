"""Refresh token: el de acceso y el de refresco no son intercambiables."""
from datetime import datetime, timedelta, timezone

from jose import jwt

from src.core.auth import create_refresh_token
from src.core.config import get_settings


def _refresh(user):
    return create_refresh_token(subject=user.usuario_id, settings=get_settings())


def test_token_de_acceso_incluye_type_access(make_user, auth):
    u = make_user()
    token = auth(u)["Authorization"].split()[1]
    s = get_settings()
    assert jwt.decode(token, s.jwt_secret_key, algorithms=[s.jwt_algorithm])["type"] == "access"


def test_token_de_acceso_sigue_funcionando(client, make_user, auth):
    u = make_user()
    assert client.get("/reportes-perdida/me", headers=auth(u)).status_code == 200


def test_refresh_token_no_sirve_como_bearer(client, make_user):
    u = make_user()
    r = client.get("/reportes-perdida/me", headers={"Authorization": f"Bearer {_refresh(u)}"})
    assert r.status_code == 401


def test_refresh_entrega_nuevo_access(client, make_user):
    u = make_user()
    rt = _refresh(u)
    r = client.post("/auth/refresh", json={"refresh_token": rt})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["refresh_token"] == rt
    nuevo = {"Authorization": f"Bearer {body['access_token']}"}
    assert client.get("/reportes-perdida/me", headers=nuevo).status_code == 200


def test_refresh_rechaza_token_de_acceso(client, make_user, auth):
    u = make_user()
    token = auth(u)["Authorization"].split()[1]
    assert client.post("/auth/refresh", json={"refresh_token": token}).status_code == 401


def test_refresh_expirado(client, make_user):
    u = make_user()
    s = get_settings()
    viejo = jwt.encode(
        {"sub": str(u.usuario_id), "type": "refresh",
         "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        s.jwt_secret_key, algorithm=s.jwt_algorithm,
    )
    assert client.post("/auth/refresh", json={"refresh_token": viejo}).status_code == 401


def test_refresh_usuario_bloqueado(client, db, make_user):
    u = make_user()
    rt = _refresh(u)
    u.is_blocked = True
    db.commit()
    assert client.post("/auth/refresh", json={"refresh_token": rt}).status_code == 403
