"""GET /analisis/{id}/fragmento: un trozo del WAV, 15 s como máximo (RF-18, 9.3; FR-008, SC-007)."""

import io
import wave

import pytest
from conftest import subir

from config import CONFIG


def preparado(api):
    return subir(api).json()["id_analisis"]


def test_devuelve_un_wav_con_el_tramo_pedido(api):
    id_analisis = preparado(api)
    respuesta = api.cliente.get(f"/analisis/{id_analisis}/fragmento?inicio=2&fin=6.5")
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == "audio/wav"
    with wave.open(io.BytesIO(respuesta.content)) as audio:
        assert audio.getnchannels() == 1
        assert audio.getframerate() == CONFIG.frecuencia_muestreo
        assert audio.getnframes() == int(4.5 * CONFIG.frecuencia_muestreo)


def test_15_segundos_justos_se_admiten(api):
    id_analisis = preparado(api)
    assert api.cliente.get(f"/analisis/{id_analisis}/fragmento?inicio=0&fin=15").status_code == 200


@pytest.mark.parametrize(
    ("inicio", "fin"),
    [
        (0, 15.01),  # más de 15 s: no se puede bajar el audio entero (9.3)
        (5, 5),  # fin no es mayor que inicio
        (6, 5),
        (-1, 3),  # antes del principio
        (40, 46),  # el audio dura 45 s
    ],
)
def test_tramos_no_validos_dan_422(api, inicio, fin):
    id_analisis = preparado(api)
    respuesta = api.cliente.get(f"/analisis/{id_analisis}/fragmento?inicio={inicio}&fin={fin}")
    assert respuesta.status_code == 422


def test_sin_wav_todavia_da_409(api):
    api.falsos.falla = "preparar"
    id_analisis = preparado(api)
    respuesta = api.cliente.get(f"/analisis/{id_analisis}/fragmento?inicio=0&fin=1")
    assert respuesta.status_code == 409
