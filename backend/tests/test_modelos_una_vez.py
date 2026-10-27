"""Los modelos se cargan una sola vez, en la primera llamada (spec 003, T051).

Cargar pyannote o inaSpeechSegmenter tarda: el servidor no puede pagarlo en cada análisis.
"""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from conftest import escribir_wav
from test_diarizacion import _Torch

from audio import diarizacion
from contrato import Turno
from voz import clasificador

TURNOS = [Turno(hablante=1, inicio=0.0, fin=1.0)]


@pytest.fixture
def wav(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setitem(sys.modules, "torch", _Torch(hay_gpu=False))
    return escribir_wav(tmp_path / "a.wav", 1.0)


def test_diarizar_carga_pyannote_una_sola_vez(wav: Path) -> None:
    with patch.object(diarizacion, "_cargar_pipeline", return_value=MagicMock()) as cargar:
        diarizacion.diarizar(wav)
        diarizacion.diarizar(wav)
    cargar.assert_called_once()


def test_proponer_voz_carga_el_segmentador_una_sola_vez(wav: Path) -> None:
    segmentador = MagicMock(return_value=[])
    with patch.object(clasificador, "_cargar_segmenter", return_value=segmentador) as cargar:
        clasificador.proponer_voz(wav, TURNOS)
        clasificador.proponer_voz(wav, TURNOS)
    cargar.assert_called_once()
    assert segmentador.call_count == 2  # el modelo sí se usa en cada llamada


def test_no_carga_nada_hasta_la_primera_llamada() -> None:
    with (
        patch.object(diarizacion, "_cargar_pipeline") as pyannote,
        patch.object(clasificador, "_cargar_segmenter") as segmentador,
    ):
        importlib.reload(importlib.import_module("api.pasos_reales"))

    pyannote.assert_not_called()
    segmentador.assert_not_called()


@pytest.mark.parametrize(
    ("modulo", "cargador"),
    [(diarizacion, "_cargar_pipeline"), (clasificador, "_cargar_segmenter")],
)
def test_si_la_carga_falla_la_siguiente_llamada_lo_vuelve_a_intentar(modulo, cargador) -> None:
    modelo = MagicMock()
    with patch.object(modulo, cargador, side_effect=[RuntimeError("sin red"), modelo]) as cargar:
        with pytest.raises(RuntimeError):
            modulo.modelo()
        assert modulo.modelo() is modelo
        assert modulo.modelo() is modelo
    assert cargar.call_count == 2
