"""Fase 1 del pipeline con los cuatro módulos reales, sin falsos (T015).

Es lenta y la CI no la ejecuta. Necesita el grupo audio, HF_TOKEN, ffmpeg y los audios de AMI
(scripts/descargar_datos.sh). Si falta algo, se salta. Desde backend/:

    uv sync --group audio && uv run pytest tests/ -m slow
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

import contrato as c
import pipeline as p

pytestmark = pytest.mark.slow

IB4002 = Path(__file__).resolve().parents[2] / "datos" / "ami" / "audios" / "IB4002.Mix-Headset.wav"


@pytest.fixture
def cinco_minutos(tmp_path):
    """Los 5 primeros minutos de IB4002, de la partición de desarrollo (11.3)."""
    if not IB4002.exists():
        pytest.skip("Falta IB4002: ejecuta scripts/descargar_datos.sh")
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg no disponible")
    destino = tmp_path / "ib4002_5min.wav"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(IB4002), "-t", "300", str(destino)],
        check=True,
        timeout=120,
    )
    return destino


@pytest.fixture
def pasos_reales():
    pytest.importorskip("pyannote.audio")
    pytest.importorskip("inaSpeechSegmenter")
    if not os.environ.get("HF_TOKEN"):
        pytest.skip("Falta HF_TOKEN")
    from analisis.analizar import analizar
    from audio.diarizacion import diarizar
    from audio.fragmentos import elegir_fragmentos
    from audio.preparar import preparar
    from voz.clasificador import proponer_voz

    return p.Pasos(
        preparar=preparar,
        diarizar=diarizar,
        proponer_voz=proponer_voz,
        elegir_fragmentos=elegir_fragmentos,
        analizar=analizar,
    )


def test_la_fase_1_real_deja_las_voces_listas_para_confirmar(tmp_path, cinco_minutos, pasos_reales):
    estados = []
    preparado = p.preparar_para_confirmar(
        "integracion", cinco_minutos, tmp_path, pasos_reales, estados.append
    )

    assert preparado is not None, estados[-1].motivo_error
    assert estados[-1].estado is c.Estado.ESPERANDO_CONFIRMACION
    hablantes = preparado.hablantes.hablantes
    assert len(hablantes) >= 2  # D-17
    for h in hablantes:
        assert h.propuesta is not None  # RF-06
        assert len(h.fragmentos) >= 3  # RF-07, D-18
    assert preparado.duracion == pytest.approx(300.0, abs=0.1)  # RF-03
    copia = c.HablantesParaConfirmar.model_validate_json(preparado.hablantes.model_dump_json())
    assert copia == preparado.hablantes
