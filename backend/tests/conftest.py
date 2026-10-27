"""Ayudas de las pruebas de la API (spec 003): pasos falsos, WAV generados y un cliente HTTP.

Nada de esto usa modelos ni GPU. Los WAV se generan en tmp_path: no entra audio en el repositorio
(constitución 7).
"""

import wave
from concurrent.futures import Future
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_pipeline import DURACION, Falsos

from config import CONFIG

EJEMPLOS = Path(__file__).parent / "ejemplos"
INICIO = datetime(2026, 10, 27, 10, 0, tzinfo=UTC)


def escribir_wav(ruta: Path, segundos: float) -> Path:
    """WAV mono 16 kHz de 16 bits con silencio, como el que deja preparar.py."""
    with wave.open(str(ruta), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(CONFIG.frecuencia_muestreo)
        audio.writeframes(b"\x00\x00" * int(segundos * CONFIG.frecuencia_muestreo))
    return ruta


def bytes_wav(tmp_path: Path, segundos: float = 1.0) -> bytes:
    return escribir_wav(tmp_path / "subir.wav", segundos).read_bytes()


class EjecutorSincrono:
    """Hace el trabajo en el momento, para que las pruebas no esperen a la cola."""

    def submit(self, funcion, *argumentos, **nombrados):
        futuro = Future()
        futuro.set_result(funcion(*argumentos, **nombrados))
        return futuro


class PasosQueEscriben(Falsos):
    """Los pasos falsos del pipeline, pero preparar deja un WAV de verdad para los fragmentos."""

    def preparar(self, origen, destino):
        super().preparar(origen, destino)
        escribir_wav(destino, DURACION)
        return DURACION


class Reloj:
    def __init__(self, ahora=INICIO):
        self.ahora = ahora

    def __call__(self):
        return self.ahora


@pytest.fixture(autouse=True)
def modelos_sin_cargar():
    """Cada prueba empieza sin modelos guardados: así puede sustituir el cargador por un falso."""
    from audio import diarizacion
    from voz import clasificador

    diarizacion.olvidar_modelo()
    clasificador.olvidar_modelo()
    yield
    diarizacion.olvidar_modelo()
    clasificador.olvidar_modelo()


@pytest.fixture
def api(tmp_path):
    """Aplicación con pasos falsos, carpeta de trabajo en tmp_path y la cola síncrona."""
    from fastapi.testclient import TestClient

    from api.ajustes import Ajustes
    from api.app import crear_app

    falsos = PasosQueEscriben()
    ajustes = Ajustes(carpeta_trabajo=tmp_path / "trabajo", ejemplos=EJEMPLOS)
    reloj = Reloj()
    duraciones = SimpleNamespace(segundos=60.0)
    app = crear_app(
        pasos=falsos.pasos(),
        ajustes=ajustes,
        ejecutor=EjecutorSincrono(),
        reloj=reloj,
        medir_duracion=lambda ruta: duraciones.segundos,
    )
    return SimpleNamespace(
        cliente=TestClient(app),
        app=app,
        falsos=falsos,
        ajustes=ajustes,
        reloj=reloj,
        duraciones=duraciones,
        tmp_path=tmp_path,
    )


def subir(api, contenido=None, nombre="reunion.wav", **campos):
    """POST /analisis con un audio (por defecto, un WAV de 1 s) y campos de formulario."""
    if contenido is None:
        contenido = bytes_wav(api.tmp_path)
    return api.cliente.post(
        "/analisis",
        files={"audio": (nombre, contenido, "audio/wav")},
        data={k: str(v).lower() for k, v in campos.items()},
    )
