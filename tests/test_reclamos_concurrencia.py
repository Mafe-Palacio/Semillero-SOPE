"""HU08: un solo reclamo activo por objeto, incluso con intentos simultáneos."""
import pytest
from sqlalchemy.exc import IntegrityError

from src.crud.ObjetoEnCustodia_crud import ObjetoEnCustodiaCRUD, ObjetoNoDisponibleError
from src.entities.Reclamos import Reclamo


def _reclamar(client, auth, user, objeto):
    return client.post(
        "/reclamos",
        headers=auth(user),
        json={
            "objetoEnCustodia_id": str(objeto.objetoEnCustodia_id),
            "usuario_id": str(user.usuario_id),
            "es_presencial": False,
        },
    )


def test_segundo_usuario_recibe_409(client, auth, make_user, objeto, db):
    a, b = make_user(), make_user()
    r1 = _reclamar(client, auth, a, objeto)
    assert r1.status_code == 201, r1.text
    r2 = _reclamar(client, auth, b, objeto)
    assert r2.status_code == 409
    assert "en curso" in r2.json()["error"]["message"] or "reclam" in r2.json()["error"]["message"].lower()
    assert db.query(Reclamo).count() == 1


def test_cancelar_libera_el_objeto(client, auth, make_user, objeto):
    a, b = make_user(), make_user()
    r1 = _reclamar(client, auth, a, objeto)
    assert client.put(f"/reclamos/{r1.json()['reclamo_id']}/cancelar", headers=auth(a)).status_code == 200
    assert _reclamar(client, auth, b, objeto).status_code == 201


def test_objeto_inexistente_404(client, auth, make_user, objeto):
    import uuid

    class Falso:
        objetoEnCustodia_id = uuid.uuid4()

    assert _reclamar(client, auth, make_user(), Falso).status_code == 404


def test_reserva_atomica_en_crud(db, objeto):
    crud = ObjetoEnCustodiaCRUD(db)
    crud.reservar_para_reclamo(objeto.objetoEnCustodia_id)
    with pytest.raises(ObjetoNoDisponibleError):
        crud.reservar_para_reclamo(objeto.objetoEnCustodia_id)


def test_indice_unico_parcial_bloquea_dos_reclamos_vivos(db, objeto, make_user):
    a, b = make_user(), make_user()
    base = dict(objetoEnCustodia_id=objeto.objetoEnCustodia_id, es_presencial=False)
    db.add(Reclamo(usuario_id=a.usuario_id, estado="ENVIADO", **base))
    db.commit()
    db.add(Reclamo(usuario_id=b.usuario_id, estado="EN_REVISION", **base))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    # un reclamo ya cerrado no cuenta como activo
    db.add(Reclamo(usuario_id=b.usuario_id, estado="RECHAZADO", **base))
    db.commit()


def test_objeto_por_vencer_sigue_reclamable_y_visible(client, auth, make_user, objeto, db):
    objeto.estado = "POR_VENCER"
    db.commit()
    u = make_user()
    catalogo = client.get("/objetos-custodia/catalogo", headers=auth(u)).json()
    assert any(o["objetoEnCustodia_id"] == str(objeto.objetoEnCustodia_id) for o in catalogo)
    assert _reclamar(client, auth, u, objeto).status_code == 201


def test_objeto_archivado_no_se_puede_reclamar(client, auth, make_user, objeto, db):
    objeto.estado = "SIN_DUENO_DEFINITIVO"
    db.commit()
    assert _reclamar(client, auth, make_user(), objeto).status_code == 409
