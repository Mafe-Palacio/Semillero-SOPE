"""HU07/HU10/CU21: las acciones quedan registradas en logs_auditoria con su autor."""
from datetime import date

from src.entities.AuditoriaLog import AuditLog
from src.entities.Ubicacion import Ubicacion


def logs(db, entidad=None):
    db.expire_all()
    q = db.query(AuditLog).order_by(AuditLog.fecha, AuditLog.auditLog_id)
    if entidad:
        q = q.filter(AuditLog.entidad == entidad)
    return [(l.entidad, l.accion.value if hasattr(l.accion, "value") else l.accion, l.usuario_id, l.detalle) for l in q.all()]


def acciones(db, entidad):
    return [x[1] for x in logs(db, entidad)]


def _publicacion(client, auth, user, punto, db):
    ub = Ubicacion(sede_id=punto.sede_id, nombre="Bloque J", tipo="BLOQUE")
    db.add(ub)
    db.commit()
    r = client.post("/publicaciones-encontradas/", headers=auth(user), json={
        "categoria": "LLAVES", "descripcion": "Llavero", "lugar_hallazgo_id": str(ub.ubicacion_id),
        "lugar_entrega_fisica_id": str(punto.puntoEntrega_id), "fecha_hallazgo": str(date.today())})
    assert r.status_code == 201, r.text
    return r.json()["publicacionEncontrado_id"]


def test_publicacion_crear_aprobar_editar_eliminar(client, auth, make_user, punto, db):
    user = make_user()
    admin = make_user(rol="ADMIN", sede_id=punto.sede_id)
    pid = _publicacion(client, auth, user, punto, db)
    assert logs(db, "PublicacionEncontrado")[0][:3] == ("PublicacionEncontrado", "CREAR", user.usuario_id)

    assert client.put(f"/publicaciones-encontradas/{pid}/moderacion", headers=auth(admin),
                      json={"estado": "APROBADA"}).status_code == 200
    r = client.put(f"/publicaciones-encontradas/{pid}", headers=auth(admin), json={"descripcion": "Llavero rojo"})
    assert r.status_code == 200, r.text
    assert client.put(f"/publicaciones-encontradas/{pid}/solicitar-eliminacion", headers=auth(user)).status_code == 200
    assert client.put(f"/publicaciones-encontradas/{pid}/resolver-eliminacion", headers=auth(admin),
                      json={"aprobar": True}).status_code == 200

    seq = logs(db, "PublicacionEncontrado")
    assert [x[1] for x in seq] == ["CREAR", "APROBAR", "EDITAR", "CAMBIO_ESTADO", "ELIMINAR"]
    assert seq[1][2] == admin.usuario_id and "PENDIENTE → APROBADA" in seq[1][3]
    assert seq[2][3] == "Campos: descripcion"     # solo nombres de campo, nunca el contenido
    assert "rojo" not in " ".join(str(x[3]) for x in seq)


def test_rechazo_queda_registrado(client, auth, make_user, punto, db):
    user = make_user()
    admin = make_user(rol="ADMIN", sede_id=punto.sede_id)
    pid = _publicacion(client, auth, user, punto, db)
    client.put(f"/publicaciones-encontradas/{pid}/moderacion", headers=auth(admin),
               json={"estado": "RECHAZADA", "motivo_rechazo": "Duplicada"})
    assert acciones(db, "PublicacionEncontrado") == ["CREAR", "RECHAZAR"]


def test_reclamo_y_entrega_con_acta(client, auth, make_user, objeto, db):
    user = make_user()
    admin = db.get(type(user), objeto.admin_id)
    body = {"objetoEnCustodia_id": str(objeto.objetoEnCustodia_id), "usuario_id": str(user.usuario_id),
            "es_presencial": False}
    rid = client.post("/reclamos", headers=auth(user), json=body).json()["reclamo_id"]
    assert client.put(f"/reclamos/{rid}", headers=auth(admin), json={"estado": "APROBADO"}).status_code == 200
    acta = client.post("/actas-entrega", headers=auth(admin), json={
        "reclamo_id": rid, "nombre_reclamante": "Ana", "cedula_reclamante": "1", "correo_reclamante": "a@b.co",
        "celular_reclamante": "300", "carnet_reclamante": "c1",
        "firma_url": "https://res.cloudinary.com/x/firma.png", "validacion_verbal": False})
    assert acta.status_code == 201, acta.text

    assert acciones(db, "Reclamo") == ["CREAR", "APROBAR", "CAMBIO_ESTADO"]  # el acta lo cierra: RECLAMADO
    assert acciones(db, "ActaEntrega") == ["CREAR"]
    assert acciones(db, "ObjetoEnCustodia") == ["CAMBIO_ESTADO"]  # EN_CUSTODIA → RECLAMADO
    assert logs(db, "ObjetoEnCustodia")[0][2] == admin.usuario_id
    assert "EN_CUSTODIA → RECLAMADO" in logs(db, "ObjetoEnCustodia")[0][3]


def test_cancelar_reclamo(client, auth, make_user, objeto, db):
    user = make_user()
    body = {"objetoEnCustodia_id": str(objeto.objetoEnCustodia_id), "usuario_id": str(user.usuario_id),
            "es_presencial": False}
    rid = client.post("/reclamos", headers=auth(user), json=body).json()["reclamo_id"]
    client.put(f"/reclamos/{rid}/cancelar", headers=auth(user))
    assert acciones(db, "Reclamo") == ["CREAR", "CAMBIO_ESTADO"]
    assert acciones(db, "ObjetoEnCustodia") == []  # reservar/liberar no es ruido de auditoría


def test_bloqueo_de_usuario(client, auth, make_user, db):
    admin = make_user(rol="SUPERADMIN")
    user = make_user()
    r = client.put(f"/usuarios/{user.usuario_id}/moderacion", headers=auth(admin),
                   json={"is_blocked": True, "motivo_bloqueo": "Spam"})
    assert r.status_code == 200, r.text
    client.put(f"/usuarios/{user.usuario_id}/moderacion", headers=auth(admin), json={"is_blocked": False})
    seq = logs(db, "Usuario")
    assert [x[1] for x in seq] == ["BLOQUEAR", "DESBLOQUEAR"]
    assert "Spam" not in str(seq)  # el motivo vive en el usuario, no se duplica en el log


def test_editar_perfil_propio_no_genera_log(client, auth, make_user, db):
    u = make_user(celular=None)
    assert client.put("/usuarios/me", headers=auth(u), json={"celular": "3001112233"}).status_code == 200
    assert logs(db) == []


def test_sin_sesion_no_se_registra_nada(client, db):
    client.get("/objetos-custodia/catalogo")
    assert logs(db) == []


def test_expiracion_registra_cambio_de_estado(client, auth, make_user, objeto, db):
    from datetime import timedelta
    admin = db.get(type(make_user()), objeto.admin_id)
    objeto.fecha_ingreso = date.today() - timedelta(days=151)
    db.commit()
    assert client.post("/objetos-custodia/expiracion", headers=auth(admin)).status_code == 200
    seq = logs(db, "ObjetoEnCustodia")
    assert [x[1] for x in seq] == ["CAMBIO_ESTADO"] and "EN_CUSTODIA → POR_VENCER" in seq[0][3]


def test_auditoria_se_consulta_por_api(client, auth, make_user, punto, db):
    user = make_user()
    admin = make_user(rol="ADMIN", sede_id=punto.sede_id)
    pid = _publicacion(client, auth, user, punto, db)
    r = client.get(f"/auditoria/entidad/PublicacionEncontrado/id/{pid}", headers=auth(admin))
    assert r.status_code == 200 and r.json()[0]["accion"] == "CREAR"
    assert client.get("/auditoria?entidad=PublicacionEncontrado", headers=auth(admin)).headers["X-Total-Count"] == "1"
