"""HU28: solo JPG/PNG, máximo 5 MB, contenido real verificado."""
import pytest

from src.utils import imagenes
from src.utils.imagenes import ImagenInvalidaError, validar_imagen

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100
JPG = b"\xff\xd8\xff\xe0" + b"0" * 100


def test_formatos_validos():
    assert validar_imagen("image/png", PNG) == "png"
    assert validar_imagen("image/jpeg", JPG) == "jpg"


@pytest.mark.parametrize("tipo,datos,codigo", [
    ("image/gif", b"GIF89a" + b"0" * 50, 415),
    ("application/pdf", b"%PDF", 415),
    (None, PNG, 415),
    ("image/png", JPG, 415),                       # dice PNG pero es JPG
    ("image/jpeg", b"<script>alert(1)</script>", 415),
    ("image/png", b"", 400),
    ("image/png", PNG + b"0" * (5 * 1024 * 1024), 413),
])
def test_rechazos(tipo, datos, codigo):
    with pytest.raises(ImagenInvalidaError) as e:
        validar_imagen(tipo, datos)
    assert e.value.status_code == codigo


def test_exactamente_5mb_pasa():
    assert validar_imagen("image/png", PNG + b"0" * (5 * 1024 * 1024 - len(PNG))) == "png"


def _con_cloudinary(monkeypatch, activo: bool):
    """Fija si el endpoint ve credenciales de Cloudinary, sin depender del .env de cada máquina."""
    from src.core.config import get_settings

    cred = {"cloudinary_cloud_name": "x", "cloudinary_api_key": "k", "cloudinary_api_secret": "s"} if activo else {
        "cloudinary_cloud_name": None, "cloudinary_api_key": None, "cloudinary_api_secret": None}
    ajustes = get_settings().model_copy(update=cred)
    monkeypatch.setattr("src.endpoints.Imagenes.get_settings", lambda: ajustes)


def test_endpoint_sube_y_devuelve_url(client, auth, make_user, monkeypatch):
    _con_cloudinary(monkeypatch, True)
    monkeypatch.setattr("src.endpoints.Imagenes.subir_a_cloudinary",
                        lambda datos, carpeta, settings: {"secure_url": "https://res.cloudinary.com/x/ope/a.png"})
    r = client.post("/imagenes", headers=auth(make_user()), files={"archivo": ("a.png", PNG, "image/png")})
    assert r.status_code == 201, r.text
    assert r.json() == {"url": "https://res.cloudinary.com/x/ope/a.png", "formato": "png", "bytes": len(PNG)}


def test_endpoint_rechaza_gif_y_grandes(client, auth, make_user, monkeypatch):
    _con_cloudinary(monkeypatch, True)
    monkeypatch.setattr("src.endpoints.Imagenes.subir_a_cloudinary", lambda *a: pytest.fail("no debe subir"))
    h = auth(make_user())
    assert client.post("/imagenes", headers=h, files={"archivo": ("a.gif", b"GIF89a", "image/gif")}).status_code == 415
    grande = PNG + b"0" * (5 * 1024 * 1024)
    assert client.post("/imagenes", headers=h, files={"archivo": ("a.png", grande, "image/png")}).status_code == 413


def test_endpoint_requiere_login(client):
    assert client.post("/imagenes", files={"archivo": ("a.png", PNG, "image/png")}).status_code == 401


def test_sin_cloudinary_guarda_local_y_la_sirve(client, auth, make_user, monkeypatch):
    """Sin credenciales de Cloudinary la imagen se guarda en uploads/ y se sirve por GET /imagenes/{archivo}."""
    from src.endpoints import Imagenes

    _con_cloudinary(monkeypatch, False)
    r = client.post("/imagenes", headers=auth(make_user()), files={"archivo": ("a.png", PNG, "image/png")})
    assert r.status_code == 201, r.text
    nombre = r.json()["url"].rsplit("/", 1)[-1]
    try:
        assert r.json()["formato"] == "png" and "/imagenes/" in r.json()["url"]
        servida = client.get(f"/imagenes/{nombre}")
        assert servida.status_code == 200 and servida.content == PNG
        assert client.get("/imagenes/../main.py").status_code in (404, 405)
    finally:
        (Imagenes.UPLOADS_DIR / nombre).unlink(missing_ok=True)


def test_url_de_imagen_debe_ser_https(client, auth, make_user, objeto):
    u = make_user()
    body = {"objetoEnCustodia_id": str(objeto.objetoEnCustodia_id), "usuario_id": str(u.usuario_id),
            "es_presencial": False}
    assert client.post("/reclamos", headers=auth(u), json={**body, "evidencia_url": "http://x.com/a.png"}).status_code == 422
    assert client.post("/reclamos", headers=auth(u), json={**body, "evidencia_url": "javascript:alert(1)"}).status_code == 422
    assert client.post("/reclamos", headers=auth(u), json={**body, "evidencia_url": "https://res.cloudinary.com/a.png"}).status_code == 201


def test_hosts_permitidos(monkeypatch):
    from src.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("IMAGE_ALLOWED_HOSTS", "res.cloudinary.com")
    try:
        assert imagenes.validar_url_imagen("https://res.cloudinary.com/a.png")
        with pytest.raises(ValueError):
            imagenes.validar_url_imagen("https://evil.example/a.png")
    finally:
        get_settings.cache_clear()
