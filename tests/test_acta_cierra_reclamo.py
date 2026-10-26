"""El acta de entrega cierra el reclamo (RECLAMADO) y el objeto."""


def _acta(rid):
    return {
        "reclamo_id": rid, "nombre_reclamante": "Juan", "cedula_reclamante": "1000000003",
        "correo_reclamante": "juan@correo.itm.edu.co", "celular_reclamante": "3003333333",
        "carnet_reclamante": "EST-1",
        "firma_url": "https://res.cloudinary.com/demo/image/upload/firma-demo.png",
        "validacion_verbal": True,
    }


def test_acta_deja_reclamo_y_objeto_en_reclamado(client, make_user, auth, objeto):
    admin = make_user(rol="ADMIN", sede_id=objeto.lugar_origen.sede_id)
    juan = make_user()
    r = client.post("/reclamos", headers=auth(juan), json={
        "objetoEnCustodia_id": str(objeto.objetoEnCustodia_id),
        "usuario_id": str(juan.usuario_id), "es_presencial": False})
    assert r.status_code == 201
    rid = r.json()["reclamo_id"]
    assert client.put(f"/reclamos/{rid}", headers=auth(admin),
                      json={"estado": "LISTO_PARA_RECOGER"}).status_code == 200
    assert client.post("/actas-entrega", headers=auth(admin), json=_acta(rid)).status_code == 201
    assert client.get(f"/reclamos/{rid}", headers=auth(admin)).json()["estado"] == "RECLAMADO"
    assert client.get(f"/objetos-custodia/{objeto.objetoEnCustodia_id}", headers=auth(admin)).json()["estado"] == "RECLAMADO"
