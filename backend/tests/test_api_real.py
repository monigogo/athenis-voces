"""Recorrido completo de la API con los modelos reales, sin falsos (spec 003, T025).

Es lenta y la CI no la ejecuta. Necesita el grupo audio, HF_TOKEN, ffmpeg y los audios de AMI
(scripts/descargar_datos.sh). Si falta algo, se salta. Usa IB4002, de la partición de desarrollo:
la de prueba solo sirve para medir (constitución 9). Desde backend/:

    uv sync --group audio && uv run --env-file ../.env pytest tests/test_api_real.py -m slow
"""

import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

import contrato as c

pytestmark = pytest.mark.slow

IB4002 = Path(__file__).resolve().parents[2] / "datos" / "ami" / "audios" / "IB4002.Mix-Headset.wav"
ESPERA_MAXIMA = 30 * 60  # segundos


def con_ffmpeg():
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        pytest.skip("ffmpeg o ffprobe no disponible")


@pytest.fixture
def cinco_minutos(tmp_path):
    """Los 5 primeros minutos de IB4002, fuera del repositorio."""
    if not IB4002.exists():
        pytest.skip("Falta IB4002: ejecuta scripts/descargar_datos.sh")
    con_ffmpeg()
    destino = tmp_path / "ib4002_5min.wav"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", f"file:{IB4002}", "-t", "300", str(destino)],
        check=True,
        timeout=120,
    )
    return destino


@pytest.fixture
def cliente(tmp_path):
    pytest.importorskip("pyannote.audio")
    pytest.importorskip("inaSpeechSegmenter")
    if not os.environ.get("HF_TOKEN"):
        pytest.skip("Falta HF_TOKEN")
    from fastapi.testclient import TestClient

    from api.ajustes import Ajustes
    from api.app import crear_app

    with TestClient(crear_app(ajustes=Ajustes(carpeta_trabajo=tmp_path / "trabajo"))) as cliente:
        yield cliente


def esperar(cliente, id_analisis, hasta):
    limite = time.monotonic() + ESPERA_MAXIMA
    while time.monotonic() < limite:
        estado = c.EstadoAnalisis.model_validate(cliente.get(f"/analisis/{id_analisis}").json())
        if estado.estado in (hasta, c.Estado.ERROR):
            return estado
        time.sleep(2)
    pytest.fail(f"El análisis no llegó a «{hasta}» en {ESPERA_MAXIMA} s")


def test_recorrido_completo_con_los_modelos_reales(cliente, cinco_minutos):
    with cinco_minutos.open("rb") as audio:
        respuesta = cliente.post("/analisis", files={"audio": ("a.wav", audio, "audio/wav")})
    assert respuesta.status_code == 201
    id_analisis = respuesta.json()["id_analisis"]

    estado = esperar(cliente, id_analisis, c.Estado.ESPERANDO_CONFIRMACION)
    assert estado.estado is c.Estado.ESPERANDO_CONFIRMACION, estado.motivo_error
    hablantes = c.HablantesParaConfirmar.model_validate(
        cliente.get(f"/analisis/{id_analisis}/hablantes").json()
    )
    assert len(hablantes.hablantes) >= 2  # D-17
    muestra = hablantes.hablantes[0].fragmentos[0]
    sonido = cliente.get(
        f"/analisis/{id_analisis}/fragmento?inicio={muestra.inicio}&fin={muestra.fin}"
    )
    assert sonido.status_code == 200

    confirmacion = c.Confirmacion(
        etiquetas=[
            c.EtiquetaConfirmada(hablante=h.hablante, etiqueta="indeterminado", origen="persona")
            for h in hablantes.hablantes
        ]
    )
    respuesta = cliente.post(
        f"/analisis/{id_analisis}/confirmacion", json=confirmacion.model_dump(mode="json")
    )
    assert respuesta.status_code == 202
    assert esperar(cliente, id_analisis, c.Estado.TERMINADO).estado is c.Estado.TERMINADO
    resultado = c.Resultado.model_validate(cliente.get(f"/analisis/{id_analisis}/resultado").json())
    assert resultado.id_analisis == id_analisis


def test_ffprobe_real_rechaza_un_falso_mp3(tmp_path):
    """Una cabecera ID3 sin audio detrás engaña a los bytes mágicos, pero no a ffprobe."""
    con_ffmpeg()
    from api.subida import medir_duracion

    falso = tmp_path / "falso.subida"
    falso.write_bytes(b"ID3" + b"\x00" * 64 + b"esto no es audio")
    with pytest.raises(ValueError):
        medir_duracion(falso)
