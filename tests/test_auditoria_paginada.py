"""HU10 / CU21: auditoría paginada de 10 en 10."""
import uuid
from datetime import datetime

from src.entities.AuditoriaLog import AuditLog


def _logs(db, admin, n, entidad="Reclamo", accion="CREAR", fecha=None):
    for i in range(n):
        db.add(AuditLog(entidad=entidad, entidad_id=uuid.uuid4(), accion=accion,
                        usuario_id=admin.usuario_id, detalle=f"log {i}",
                        fecha=fecha or datetime.utcnow()))
    db.commit()


def test_paginas_de_diez(client, auth, make_user, db):
    admin = make_user(rol="ADMIN")
    _logs(db, admin, 25)
    p1 = client.get("/auditoria", headers=auth(admin))
    assert len(p1.json()) == 10
    assert p1.headers["X-Total-Count"] == "25"
    assert p1.headers["X-Total-Paginas"] == "3"
    assert p1.headers["X-Tamano-Pagina"] == "10"
    assert len(client.get("/auditoria?pagina=3", headers=auth(admin)).json()) == 5
    assert client.get("/auditoria?pagina=4", headers=auth(admin)).json() == []


def test_no_se_puede_pedir_mas_de_diez(client, auth, make_user, db):
    admin = make_user(rol="ADMIN")
    _logs(db, admin, 15)
    assert len(client.get("/auditoria?limit=100", headers=auth(admin)).json()) == 10


def test_filtros_por_accion_entidad_y_fechas(client, auth, make_user, db):
    admin = make_user(rol="ADMIN")
    _logs(db, admin, 3, entidad="Reclamo", accion="APROBAR", fecha=datetime(2026, 1, 10, 12))
    _logs(db, admin, 4, entidad="Usuario", accion="BLOQUEAR", fecha=datetime(2026, 2, 20, 12))
    h = auth(admin)
    assert client.get("/auditoria?accion=APROBAR", headers=h).headers["X-Total-Count"] == "3"
    assert client.get("/auditoria?entidad=Usuario", headers=h).headers["X-Total-Count"] == "4"
    r = client.get("/auditoria?fecha_desde=2026-02-01&fecha_hasta=2026-02-20", headers=h)
    assert r.headers["X-Total-Count"] == "4"  # fecha_hasta es inclusiva
    assert client.get("/auditoria?pagina=0", headers=h).status_code == 422


def test_solo_admin(client, auth, make_user):
    assert client.get("/auditoria", headers=auth(make_user())).status_code == 403
