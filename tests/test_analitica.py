"""Listados de coincidencias y actas, métricas del dashboard y exportación CSV/Excel."""
import csv
import io
from datetime import date, datetime, timedelta, timezone


def _hoy_utc() -> date:
    """Las fechas del back se guardan en UTC (datetime.utcnow); usar la fecha local
    haría fallar estos tests entre las 7 p. m. y medianoche en Colombia."""
    return datetime.now(timezone.utc).date()
from uuid import UUID

import pytest
from openpyxl import load_workbook

from src.entities.ObjetoEnCustodia import ObjetoEnCustodia
from src.entities.PosibleCoincidencia import PosibleCoincidencia
from src.entities.Sede import Sede
from src.entities.Ubicacion import Ubicacion

ACTA = {
    "nombre_reclamante": "Juan", "cedula_reclamante": "1000000003",
    "correo_reclamante": "juan@correo.itm.edu.co", "celular_reclamante": "3003333333",
    "carnet_reclamante": "EST-1",
    "firma_url": "https://res.cloudinary.com/demo/image/upload/firma-demo.png",
    "validacion_verbal": True,
}


@pytest.fixture()
def escenario(client, db, make_user, auth, punto, objeto):
    """Un objeto ya entregado (con acta), otro sin reclamar y un reporte de pérdida."""
    admin = make_user(rol="ADMIN", sede_id=punto.sede_id)
    juan = make_user()
    objeto.fecha_ingreso = _hoy_utc() - timedelta(days=10)
    db.add(ObjetoEnCustodia(admin_id=admin.usuario_id, categoria="ELECTRONICOS",
                            descripcion="=HYPERLINK(\"http://malo\")", lugar_origen_id=punto.puntoEntrega_id,
                            fecha_ingreso=_hoy_utc()))
    ub = Ubicacion(sede_id=punto.sede_id, nombre="Bloque J", tipo="BLOQUE")
    db.add(ub)
    db.commit()

    rid = client.post("/reclamos", headers=auth(juan), json={
        "objetoEnCustodia_id": str(objeto.objetoEnCustodia_id), "es_presencial": False}).json()["reclamo_id"]
    client.put(f"/reclamos/{rid}", headers=auth(admin), json={"estado": "LISTO_PARA_RECOGER"})
    acta = client.post("/actas-entrega", headers=auth(admin), json={**ACTA, "reclamo_id": rid})
    assert acta.status_code == 201, acta.text

    r = client.post("/reportes-perdida/", headers=auth(juan), json={
        "categoria": "ELECTRONICOS", "descripcion": "Audífonos", "lugar_perdida_id": str(ub.ubicacion_id),
        "fecha_perdida": str(date.today())})
    assert r.status_code == 201, r.text
    return {"admin": admin, "juan": juan, "objeto": objeto, "reporte_id": r.json()["reportePerdida_id"],
            "acta_id": acta.json()["actaEntrega_id"]}


# ---------------- listados ----------------

def test_listar_actas_con_total_y_filtros(client, auth, escenario):
    h = auth(escenario["admin"])
    r = client.get("/actas-entrega", headers=h)
    assert r.status_code == 200 and r.headers["X-Total-Count"] == "1"
    assert r.json()[0]["actaEntrega_id"] == escenario["acta_id"]
    hoy = _hoy_utc().isoformat()
    assert client.get(f"/actas-entrega?fecha_desde={hoy}&fecha_hasta={hoy}", headers=h).headers["X-Total-Count"] == "1"
    ayer = (_hoy_utc() - timedelta(days=1)).isoformat()
    assert client.get(f"/actas-entrega?fecha_hasta={ayer}", headers=h).json() == []
    assert client.get("/actas-entrega?validacion_verbal=false", headers=h).json() == []
    assert client.get("/actas-entrega?limit=500", headers=h).status_code == 422


def test_actas_son_de_la_sede_y_solo_admin(client, auth, make_user, db, escenario):
    otra = Sede(nombre="Robledo", codigo="ROB")
    db.add(otra)
    db.commit()
    ajeno = make_user(rol="ADMIN", sede_id=otra.sede_id)
    assert client.get("/actas-entrega", headers=auth(ajeno)).json() == []
    assert client.get("/actas-entrega", headers=auth(escenario["juan"])).status_code == 403
    sa = make_user(rol="SUPERADMIN")
    assert client.get("/actas-entrega", headers=auth(sa)).status_code == 400  # sin sede elegida
    h = {**auth(sa), "X-Sede-Id": str(escenario["objeto"].lugar_origen.sede_id)}
    assert client.get("/actas-entrega", headers=h).headers["X-Total-Count"] == "1"


def test_listar_coincidencias_con_detalle(client, auth, db, escenario):
    db.add(PosibleCoincidencia(objetoEnCustodia_id=escenario["objeto"].objetoEnCustodia_id,
                               reportePerdida_id=UUID(escenario["reporte_id"]),
                               usuario_id=escenario["juan"].usuario_id, score=80))
    db.commit()
    h = auth(escenario["admin"])
    r = client.get("/posibles-coincidencias", headers=h)
    assert r.status_code == 200 and r.headers["X-Total-Count"] == "1"
    fila = r.json()[0]
    assert fila["score"] == 80 and fila["reporte_descripcion"] == "Audífonos"
    assert fila["usuario_nombre"] == escenario["juan"].nombre_completo
    assert client.get("/posibles-coincidencias?score_minimo=90", headers=h).json() == []
    assert client.get("/posibles-coincidencias?notificado=true", headers=h).json() == []
    assert client.get("/posibles-coincidencias", headers=auth(escenario["juan"])).status_code == 403


# ---------------- métricas ----------------

def test_metricas_del_dashboard(client, auth, escenario):
    r = client.get("/metricas/resumen", headers=auth(escenario["admin"]))
    assert r.status_code == 200, r.text
    m = r.json()
    assert m["total_objetos"] == 2 and m["reclamados"] == 1 and m["sin_reclamar"] == 1
    assert m["porcentaje_devueltos"] == 50.0
    assert m["objetos_por_estado"]["RECLAMADO"] == 1
    assert m["dias_promedio_custodia"] == 10.0
    assert m["categorias_mas_perdidas"] == [{"categoria": "ELECTRONICOS", "total": 1}]
    assert m["reclamos_por_estado"] == {"RECLAMADO": 1}
    assert m["pendientes_aprobacion"]["reportes_perdida"] == 1


def test_metricas_filtran_por_fecha_y_validan_rango(client, auth, escenario):
    h = auth(escenario["admin"])
    hoy = _hoy_utc().isoformat()
    assert client.get(f"/metricas/resumen?fecha_desde={hoy}", headers=h).json()["total_objetos"] == 1
    assert client.get(f"/metricas/resumen?fecha_desde={hoy}&fecha_hasta=2020-01-01", headers=h).status_code == 400


def test_metricas_vacias_no_fallan(client, auth, make_user, sede):
    admin = make_user(rol="ADMIN", sede_id=sede.sede_id)
    m = client.get("/metricas/resumen", headers=auth(admin)).json()
    assert m["total_objetos"] == 0 and m["porcentaje_devueltos"] == 0.0 and m["dias_promedio_custodia"] is None


def test_metricas_exigen_admin(client, auth, escenario):
    assert client.get("/metricas/resumen", headers=auth(escenario["juan"])).status_code == 403


# ---------------- exportación ----------------

def test_exportar_entregas_csv(client, auth, escenario):
    r = client.get("/exportaciones/entregas?formato=csv", headers=auth(escenario["admin"]))
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert 'attachment; filename="entregas_' in r.headers["content-disposition"]
    texto = r.content.decode("utf-8-sig")
    filas = list(csv.reader(io.StringIO(texto)))
    assert filas[0][:3] == ["Fecha y hora de entrega", "Reclamante", "Cédula"]
    assert len(filas) == 2 and filas[1][1] == "Juan" and filas[1][9] == "10"  # días en custodia


def test_exportar_xlsx_y_neutraliza_formulas(client, auth, escenario):
    r = client.get("/exportaciones/objetos-custodia?formato=xlsx", headers=auth(escenario["admin"]))
    assert r.status_code == 200 and "spreadsheetml" in r.headers["content-type"]
    hoja = load_workbook(io.BytesIO(r.content)).active
    assert [c.value for c in hoja[1]][:2] == ["Fecha de ingreso", "Categoría"]
    descripciones = [hoja.cell(row=i, column=3).value for i in range(2, hoja.max_row + 1)]
    assert hoja.max_row == 3
    texto_malo = next(d for d in descripciones if "HYPERLINK" in d)
    assert texto_malo.startswith("'=")           # una fórmula escrita por un usuario no se ejecuta
    assert load_workbook(io.BytesIO(r.content)).active.cell(row=2, column=3).data_type != "f"


def test_exportar_filtros_y_otros_recursos(client, auth, escenario):
    h = auth(escenario["admin"])
    r = client.get("/exportaciones/objetos-custodia?formato=csv&estado=RECLAMADO", headers=h)
    assert len(list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))) == 2
    r = client.get("/exportaciones/reportes-perdida?formato=csv&categoria=ELECTRONICOS", headers=h)
    assert "Audífonos" in r.content.decode("utf-8-sig")
    assert client.get("/exportaciones/reportes-perdida?formato=csv&categoria=LLAVES", headers=h).content.decode("utf-8-sig").count("\n") == 1
    assert client.get("/exportaciones/publicaciones-encontradas?formato=csv", headers=h).status_code == 200


def test_exportar_validaciones_y_permisos(client, auth, escenario):
    h = auth(escenario["admin"])
    assert client.get("/exportaciones/secretos", headers=h).status_code == 422
    assert client.get("/exportaciones/entregas?formato=pdf", headers=h).status_code == 422
    assert client.get("/exportaciones/entregas?fecha_desde=2026-02-01&fecha_hasta=2026-01-01", headers=h).status_code == 400
    assert client.get("/exportaciones/entregas", headers=auth(escenario["juan"])).status_code == 403
