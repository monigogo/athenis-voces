"""Recorrido mínimo por la API: estado, hablantes, confirmación y resultado (spec 003, US1–US3)."""

from conftest import subir

import contrato as c


def subido(api):
    return subir(api).json()["id_analisis"]


def confirmacion(hablantes=(1, 2), etiqueta="femenino", origen="persona"):
    return {
        "version_contrato": c.VERSION_CONTRATO,
        "etiquetas": [{"hablante": h, "etiqueta": etiqueta, "origen": origen} for h in hablantes],
    }


# --- Estado (RF-04, FR-003) --------------------------------------------------------------------


def test_el_estado_llega_a_esperando_confirmacion(api):
    id_analisis = subido(api)
    estado = c.EstadoAnalisis.model_validate(api.cliente.get(f"/analisis/{id_analisis}").json())
    assert estado.estado is c.Estado.ESPERANDO_CONFIRMACION
    assert api.falsos.llamadas == ["preparar", "diarizar", "proponer_voz", "elegir_fragmentos"]


def test_un_paso_que_falla_deja_el_error_con_su_motivo(api):
    api.falsos.falla = "diarizar"
    id_analisis = subido(api)
    estado = api.cliente.get(f"/analisis/{id_analisis}").json()
    assert estado["estado"] == "error"
    assert "separar las voces" in estado["motivo_error"]


def test_un_analisis_que_no_existe_da_404(api):
    for ruta in ("", "/hablantes", "/resultado", "/fragmento?inicio=0&fin=1"):
        assert api.cliente.get(f"/analisis/no-existe{ruta}").status_code == 404
    assert (
        api.cliente.post("/analisis/no-existe/confirmacion", json=confirmacion()).status_code == 404
    )


# --- Hablantes (RF-07, FR-005) -----------------------------------------------------------------


def test_hablantes_solo_trae_las_voces_presentes(api):
    id_analisis = subido(api)
    respuesta = api.cliente.get(f"/analisis/{id_analisis}/hablantes")
    assert respuesta.status_code == 200
    hablantes = c.HablantesParaConfirmar.model_validate(respuesta.json())
    assert hablantes.id_analisis == id_analisis
    assert [h.hablante for h in hablantes.hablantes] == [1, 2]  # el 3 es una voz corta
    assert all(h.propuesta is not None for h in hablantes.hablantes)


def test_hablantes_antes_de_tiempo_da_409(api):
    api.falsos.falla = "diarizar"
    id_analisis = subido(api)
    assert api.cliente.get(f"/analisis/{id_analisis}/hablantes").status_code == 409


# --- Confirmación (RF-07, FR-005, FR-006) ------------------------------------------------------


def test_confirmar_lleva_a_terminado(api):
    id_analisis = subido(api)
    respuesta = api.cliente.post(f"/analisis/{id_analisis}/confirmacion", json=confirmacion())
    assert respuesta.status_code == 202
    assert c.EstadoAnalisis.model_validate(respuesta.json()).id_analisis == id_analisis
    assert api.cliente.get(f"/analisis/{id_analisis}").json()["estado"] == "terminado"


def test_la_confirmacion_llega_al_analisis_con_su_origen(api):
    id_analisis = subido(api)
    api.cliente.post(f"/analisis/{id_analisis}/confirmacion", json=confirmacion(origen="modelo"))
    etiquetas = api.falsos.entrada.etiquetas
    assert [(e.hablante, e.etiqueta, e.origen) for e in etiquetas] == [
        (1, c.EtiquetaVoz.FEMENINO, c.OrigenEtiqueta.MODELO),
        (2, c.EtiquetaVoz.FEMENINO, c.OrigenEtiqueta.MODELO),
    ]


def test_confirmar_otras_voces_da_422_y_no_cambia_el_estado(api):
    id_analisis = subido(api)
    for hablantes in [(1,), (1, 2, 3)]:
        respuesta = api.cliente.post(
            f"/analisis/{id_analisis}/confirmacion", json=confirmacion(hablantes)
        )
        assert respuesta.status_code == 422
    assert api.cliente.get(f"/analisis/{id_analisis}").json()["estado"] == "esperando_confirmacion"


def test_un_cuerpo_que_no_cumple_el_contrato_da_422(api):
    id_analisis = subido(api)
    malo = confirmacion() | {"version_contrato": "0.1"}
    assert api.cliente.post(f"/analisis/{id_analisis}/confirmacion", json=malo).status_code == 422
    sin_tres_opciones = confirmacion(etiqueta="mujer")
    respuesta = api.cliente.post(f"/analisis/{id_analisis}/confirmacion", json=sin_tres_opciones)
    assert respuesta.status_code == 422


def test_confirmar_dos_veces_da_409(api):
    id_analisis = subido(api)
    api.cliente.post(f"/analisis/{id_analisis}/confirmacion", json=confirmacion())
    respuesta = api.cliente.post(f"/analisis/{id_analisis}/confirmacion", json=confirmacion())
    assert respuesta.status_code == 409


# --- Resultado (RF-17, FR-007) -----------------------------------------------------------------


def test_el_resultado_lleva_el_identificador_del_analisis(api):
    id_analisis = subido(api)
    api.cliente.post(f"/analisis/{id_analisis}/confirmacion", json=confirmacion())
    respuesta = api.cliente.get(f"/analisis/{id_analisis}/resultado")
    assert respuesta.status_code == 200
    assert c.Resultado.model_validate(respuesta.json()).id_analisis == id_analisis


def test_el_resultado_antes_de_terminar_da_409(api):
    id_analisis = subido(api)
    assert api.cliente.get(f"/analisis/{id_analisis}/resultado").status_code == 409
