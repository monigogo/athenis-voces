"""Modo manual (RF-08; spec 003, T036): con él activo, el clasificador de voz no se ejecuta."""

from conftest import subir


def test_con_modo_manual_no_se_llama_al_clasificador(api):
    api.falsos.falla = "proponer_voz"  # si se le llamara, el análisis acabaría en error
    id_analisis = subir(api, modo_manual=True).json()["id_analisis"]
    assert "proponer_voz" not in api.falsos.llamadas
    assert api.cliente.get(f"/analisis/{id_analisis}").json()["estado"] == "esperando_confirmacion"
    hablantes = api.cliente.get(f"/analisis/{id_analisis}/hablantes").json()["hablantes"]
    assert [h["propuesta"] for h in hablantes] == [None, None]


def test_sin_el_campo_se_propone_la_voz(api):
    subir(api)
    assert "proponer_voz" in api.falsos.llamadas


def test_modo_manual_falso_propone_la_voz(api):
    subir(api, modo_manual=False)
    assert "proponer_voz" in api.falsos.llamadas


def test_un_valor_raro_de_modo_manual_se_rechaza(api):
    respuesta = subir(api, modo_manual="quizas")
    assert respuesta.status_code == 400
    assert not api.ajustes.carpeta_trabajo.exists() or not any(
        api.ajustes.carpeta_trabajo.iterdir()
    )
