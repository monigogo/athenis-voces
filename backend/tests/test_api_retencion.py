"""Retención de 24 h [VALIDAR] (RF-23, RNF-12; spec 003, US6, FR-011, SC-006).

Pasado el plazo no queda audio en disco; solo los datos agregados del resultado.
"""

import os
import threading
from datetime import timedelta

import pytest
from conftest import INICIO, subir
from test_api_recorrido import confirmacion

PLAZO = timedelta(hours=24)


def ficheros(api):
    return sorted(p.name for p in api.ajustes.carpeta_trabajo.iterdir())


def pasar(api, tiempo):
    api.reloj.ahora = INICIO + tiempo
    api.app.state.borrar_caducados()


def test_pasado_el_plazo_se_borran_el_audio_y_el_wav_y_queda_el_resultado(api):
    id_analisis = subir(api).json()["id_analisis"]
    api.cliente.post(f"/analisis/{id_analisis}/confirmacion", json=confirmacion())
    assert ficheros(api) == [f"{id_analisis}.subida", f"{id_analisis}.wav"]
    pasar(api, PLAZO + timedelta(seconds=1))
    assert ficheros(api) == []
    assert api.cliente.get(f"/analisis/{id_analisis}/resultado").status_code == 200
    assert api.cliente.get(f"/analisis/{id_analisis}").json()["estado"] == "terminado"


def test_antes_del_plazo_no_se_toca_nada(api):
    id_analisis = subir(api).json()["id_analisis"]
    pasar(api, PLAZO)  # justo 24 h: todavía no ha pasado el plazo
    assert ficheros(api) == [f"{id_analisis}.subida", f"{id_analisis}.wav"]
    assert api.cliente.get(f"/analisis/{id_analisis}/hablantes").status_code == 200


def test_un_analisis_sin_terminar_acaba_en_error_con_su_motivo(api):
    id_analisis = subir(api).json()["id_analisis"]
    pasar(api, PLAZO + timedelta(seconds=1))
    estado = api.cliente.get(f"/analisis/{id_analisis}").json()
    assert estado["estado"] == "error"
    assert "retención" in estado["motivo_error"]


def test_tras_la_retencion_hablantes_y_fragmento_dan_410(api):
    id_analisis = subir(api).json()["id_analisis"]
    pasar(api, PLAZO + timedelta(seconds=1))
    assert api.cliente.get(f"/analisis/{id_analisis}/hablantes").status_code == 410
    respuesta = api.cliente.get(f"/analisis/{id_analisis}/fragmento?inicio=0&fin=1")
    assert respuesta.status_code == 410


VIEJO = PLAZO + timedelta(minutes=1)
HEX_A, HEX_B = "a" * 32, "0123456789abcdef" * 2


def huerfano(api, nombre, edad):
    """Un fichero que no está en el registro, por ejemplo tras reiniciar el servidor."""
    carpeta = api.ajustes.carpeta_trabajo
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / nombre
    ruta.write_bytes(b"x")
    momento = (INICIO - edad).timestamp()
    os.utime(ruta, (momento, momento))
    return ruta


def test_borra_los_ficheros_huerfanos_viejos_y_no_los_jovenes(api):
    huerfano(api, f"{HEX_A}.subida", VIEJO)
    huerfano(api, f"{HEX_A}.wav", VIEJO)
    huerfano(api, f"{HEX_B}.wav", timedelta(hours=1))
    pasar(api, timedelta(0))
    assert ficheros(api) == [f"{HEX_B}.wav"]


@pytest.mark.parametrize(
    "nombre",
    [
        "notas.txt",
        "viejo.subida",  # no es un identificador del sistema
        f"{HEX_A}.txt",  # extensión que no es del servidor
        f"{HEX_A[:31]}.wav",  # 31 caracteres
        f"{HEX_A}0.wav",  # 33 caracteres
        f"{'A' * 32}.wav",  # mayúsculas: uuid4().hex siempre va en minúsculas
        f"{'g' * 32}.subida",  # no es hexadecimal
        f"{HEX_A}.subida.bak",
    ],
)
def test_un_fichero_viejo_con_otro_nombre_sobrevive(api, nombre):
    huerfano(api, nombre, VIEJO)
    pasar(api, timedelta(0))
    assert ficheros(api) == [nombre]


def test_un_fichero_que_desaparece_mientras_se_revisa_no_rompe_nada(api, monkeypatch):
    from pathlib import Path

    huerfano(api, f"{HEX_A}.wav", VIEJO)
    fantasma = api.ajustes.carpeta_trabajo / f"{HEX_B}.subida"  # lo borra otro antes del stat
    original = Path.iterdir
    monkeypatch.setattr(Path, "iterdir", lambda self: iter([*original(self), fantasma]))
    pasar(api, timedelta(0))
    assert os.listdir(api.ajustes.carpeta_trabajo) == []  # el viejo se borró igualmente


def test_los_ejemplos_no_caducan(api):
    respuesta = api.cliente.post(
        "/analisis", files={"ejemplo": (None, "ejemplo-con-voces-femeninas")}
    )
    id_analisis = respuesta.json()["id_analisis"]
    pasar(api, PLAZO * 3)
    assert api.cliente.get(f"/analisis/{id_analisis}/resultado").status_code == 200


def test_el_servidor_borra_periodicamente_mientras_esta_en_marcha(api):
    from fastapi.testclient import TestClient

    with TestClient(api.app):
        hilo = api.app.state.hilo_retencion
        assert hilo.is_alive()
    hilo.join(timeout=5)
    assert not hilo.is_alive()


def test_un_borrado_que_falla_no_detiene_el_hilo():
    from api.retencion import en_marcha

    llamadas, segunda = [], threading.Event()

    def borrar():
        llamadas.append(1)
        if len(llamadas) == 1:
            raise OSError("disco ocupado")
        segunda.set()

    parar = threading.Event()
    hilo = en_marcha(borrar, parar, cada=0.01)
    try:
        assert segunda.wait(timeout=5), "el hilo no volvió a llamar a borrar tras el fallo"
        assert hilo.is_alive()
    finally:
        parar.set()
        hilo.join(timeout=5)
    assert len(llamadas) >= 2
