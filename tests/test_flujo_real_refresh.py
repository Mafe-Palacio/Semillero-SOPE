"""Flujo real: login con contraseña -> usar token -> refresh -> usar token nuevo."""
import time

from src.utils.security import hash_password


def test_login_refresh_y_uso_del_token_nuevo(client, db, make_user):
    u = make_user()
    u.hashed_password = hash_password("Clave123!")
    db.commit()

    r = client.post("/auth/login", json={"correo": u.correo, "password": "Clave123!"})
    assert r.status_code == 200
    at, rt = r.json()["access_token"], r.json()["refresh_token"]
    assert client.get("/reportes-perdida/me", headers={"Authorization": f"Bearer {at}"}).status_code == 200

    time.sleep(1.1)  # para que el token nuevo tenga otro `iat`
    r2 = client.post("/auth/refresh", json={"refresh_token": rt})
    assert r2.status_code == 200
    nuevo = r2.json()["access_token"]
    assert nuevo != at
    assert client.get("/reportes-perdida/me", headers={"Authorization": f"Bearer {nuevo}"}).status_code == 200


def test_refresh_exige_campo_refresh_token(client):
    # El frontend debe mandar exactamente {"refresh_token": "..."}
    assert client.post("/auth/refresh", json={"refreshToken": "x"}).status_code == 422
