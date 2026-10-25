"""Tests para backend/scripts/analizar_audio.py (T019).

TDD: estos tests deben fallar antes de que exista el script.

preparar y diarizar están simuladas para no descargar modelos ni necesitar HF_TOKEN.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BACKEND_DIR / "scripts"


def _cargar_modulo():
    """Importa analizar_audio.py por ruta de fichero."""
    script = SCRIPTS_DIR / "analizar_audio.py"
    spec = importlib.util.spec_from_file_location("analizar_audio", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def mod():
    return _cargar_modulo()


def _turno(inicio: float, fin: float, hablante: int):
    t = MagicMock()
    t.inicio = inicio
    t.fin = fin
    t.hablante = hablante
    return t


# --- Nombre base ----------------------------------------------------------------


def test_nombre_base_strip_mix_headset(mod):
    """datos/ami/audios/EN2002a.Mix-Headset.wav → EN2002a (caso del reto)."""
    assert mod._nombre_base(Path("EN2002a.Mix-Headset.wav")) == "EN2002a"


def test_nombre_base_strip_mix_headset_ruta_completa(mod):
    """Ruta completa con Mix-Headset produce solo el identificador de reunión."""
    assert mod._nombre_base(Path("datos/ami/audios/EN2002a.Mix-Headset.wav")) == "EN2002a"


def test_nombre_base_sin_sufijo_mix_headset(mod):
    """Audio sin sufijo .Mix-Headset: solo se quita la extensión."""
    assert mod._nombre_base(Path("reunion.wav")) == "reunion"


# --- Escritura del RTTM ---------------------------------------------------------


def test_escribe_rttm_con_formato_correcto(tmp_path, mod):
    """El RTTM generado tiene el formato NIST (10 columnas) y los hablantes numerados."""
    turnos = [_turno(0.0, 5.0, 1), _turno(6.0, 10.5, 2)]
    audio = tmp_path / "EN2002a.Mix-Headset.wav"
    audio.touch()
    salida = tmp_path / "salidas"

    with (
        patch.object(mod, "_raiz_repositorio", return_value=None),
        patch("audio.preparar.preparar", return_value=10.5),
        patch("audio.diarizacion.diarizar", return_value=(turnos, [])),
    ):
        rttm = mod.analizar(audio, salida)

    assert rttm == salida / "EN2002a.rttm"
    assert rttm.exists()
    lineas = rttm.read_text(encoding="utf-8").splitlines()
    assert len(lineas) == 2

    # primera línea: 10 campos, hablante_1
    c = lineas[0].split()
    assert len(c) == 10
    assert c[0] == "SPEAKER"
    assert c[1] == "EN2002a"
    assert c[2] == "1"
    assert float(c[3]) == pytest.approx(0.0)
    assert float(c[4]) == pytest.approx(5.0)
    assert c[5] == "<NA>"
    assert c[6] == "<NA>"
    assert c[7] == "hablante_1"
    assert c[8] == "<NA>"
    assert c[9] == "<NA>"

    # segunda línea: 10 campos, hablante_2
    c2 = lineas[1].split()
    assert len(c2) == 10
    assert float(c2[3]) == pytest.approx(6.0)
    assert float(c2[4]) == pytest.approx(4.5)
    assert c2[7] == "hablante_2"


def test_hablantes_sin_espacios_en_rttm(tmp_path, mod):
    """Los nombres de hablante no contienen espacios (evaluar.py separa por espacios, campo 8)."""
    turnos = [_turno(0.0, 3.0, 1), _turno(3.0, 6.0, 2), _turno(6.0, 9.0, 3)]
    audio = tmp_path / "reunion.wav"
    audio.touch()
    salida = tmp_path / "salidas"

    with (
        patch.object(mod, "_raiz_repositorio", return_value=None),
        patch("audio.preparar.preparar", return_value=9.0),
        patch("audio.diarizacion.diarizar", return_value=(turnos, [])),
    ):
        rttm = mod.analizar(audio, salida)

    for linea in rttm.read_text(encoding="utf-8").splitlines():
        hablante = linea.split()[7]
        assert " " not in hablante
        assert hablante.startswith("hablante_")


# --- Rechazo de rutas dentro del repositorio (RD-04) ----------------------------


def test_rechaza_salida_dentro_del_repositorio(tmp_path, mod):
    """Carpeta de salida dentro del repositorio: ValueError con 'dentro del repositorio'."""
    audio = tmp_path / "audio.wav"
    audio.touch()
    repo = tmp_path / "repo"
    repo.mkdir()
    carpeta_dentro = repo / "datos" / "salidas"

    with (
        patch.object(mod, "_raiz_repositorio", return_value=repo),
        pytest.raises(ValueError, match="dentro del repositorio"),
    ):
        mod.analizar(audio, carpeta_dentro)


def test_acepta_salida_fuera_del_repositorio(tmp_path, mod):
    """Carpeta de salida fuera del repositorio: se crea y se escribe el RTTM."""
    audio = tmp_path / "audio.wav"
    audio.touch()
    repo = tmp_path / "repo"
    repo.mkdir()
    fuera = tmp_path / "salidas"  # hermana del repo, no dentro

    with (
        patch.object(mod, "_raiz_repositorio", return_value=repo),
        patch("audio.preparar.preparar", return_value=5.0),
        patch("audio.diarizacion.diarizar", return_value=([_turno(0.0, 5.0, 1)], [])),
    ):
        rttm = mod.analizar(audio, fuera)

    assert rttm.exists()
