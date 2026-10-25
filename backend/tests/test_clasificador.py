"""Tests para voz/clasificador.py (T009).

TDD: todos los tests deben fallar antes de que exista la implementación.

El import de inaSpeechSegmenter va DENTRO de _cargar_segmenter(), así que los tests
parchean esa función interna sin necesitar TensorFlow instalado.

Convención de mock:
  - _mock_segmenter(segmentos) → crea un Segmenter falso cuya llamada devuelve
    la lista de (etiqueta, inicio_s, fin_s) indicada.
  - PATCH apunta a voz.clasificador._cargar_segmenter, que es la única función
    que hace el import real.
"""

import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from contrato import EtiquetaVoz, Turno

PATCH = "voz.clasificador._cargar_segmenter"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _crear_wav(ruta: Path, duracion_s: float = 5.0) -> None:
    """WAV mono 16 kHz con silencio: argumento válido para proponer_voz."""
    framerate = 16_000
    with wave.open(str(ruta), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        wf.writeframes(b"\x00\x00" * int(framerate * duracion_s))


def _mock_segmenter(segmentos: list[tuple[str, float, float]]) -> MagicMock:
    """Mock de _cargar_segmenter: devuelve un Segmenter cuya llamada da segmentos fijos."""
    seg = MagicMock()
    seg.return_value = segmentos
    return seg


def _turno(hablante: int, inicio: float, fin: float) -> Turno:
    return Turno(hablante=hablante, inicio=inicio, fin=fin)


# ---------------------------------------------------------------------------
# Etiquetas claras
# ---------------------------------------------------------------------------


def test_voz_femenina(tmp_path: Path) -> None:
    """100 % female → femenino, confianza ∈ (0.65, 1] (RF-06)."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav)
    turnos = [_turno(1, 0.0, 5.0)]
    segmentos = [("female", 0.0, 5.0)]

    from voz.clasificador import proponer_voz

    with patch(PATCH, return_value=_mock_segmenter(segmentos)):
        resultado = proponer_voz(wav, turnos)

    propuesta = resultado[1]
    assert propuesta.etiqueta == EtiquetaVoz.FEMENINO
    assert 0.65 < propuesta.confianza <= 1.0


def test_voz_masculina(tmp_path: Path) -> None:
    """100 % male → masculino, confianza ∈ (0.65, 1]."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav)
    turnos = [_turno(1, 0.0, 5.0)]
    segmentos = [("male", 0.0, 5.0)]

    from voz.clasificador import proponer_voz

    with patch(PATCH, return_value=_mock_segmenter(segmentos)):
        resultado = proponer_voz(wav, turnos)

    propuesta = resultado[1]
    assert propuesta.etiqueta == EtiquetaVoz.MASCULINO
    assert 0.65 < propuesta.confianza <= 1.0


def test_mezcla_70_femenino(tmp_path: Path) -> None:
    """70 % female / 30 % male → femenino, confianza == 0.7."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav, 10.0)
    turnos = [_turno(1, 0.0, 10.0)]
    segmentos = [("female", 0.0, 7.0), ("male", 7.0, 10.0)]

    from voz.clasificador import proponer_voz

    with patch(PATCH, return_value=_mock_segmenter(segmentos)):
        resultado = proponer_voz(wav, turnos)

    assert resultado[1].etiqueta == EtiquetaVoz.FEMENINO
    assert abs(resultado[1].confianza - 0.7) < 1e-9


def test_mezcla_20_femenino(tmp_path: Path) -> None:
    """20 % female / 80 % male → masculino, confianza == 0.8."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav, 10.0)
    turnos = [_turno(1, 0.0, 10.0)]
    segmentos = [("female", 0.0, 2.0), ("male", 2.0, 10.0)]

    from voz.clasificador import proponer_voz

    with patch(PATCH, return_value=_mock_segmenter(segmentos)):
        resultado = proponer_voz(wav, turnos)

    assert resultado[1].etiqueta == EtiquetaVoz.MASCULINO
    assert abs(resultado[1].confianza - 0.8) < 1e-9


# ---------------------------------------------------------------------------
# Zona dudosa (FR-004, RN-03)
# ---------------------------------------------------------------------------


def test_zona_dudosa_50_50(tmp_path: Path) -> None:
    """50 % female / 50 % male → indeterminado."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav, 10.0)
    turnos = [_turno(1, 0.0, 10.0)]
    segmentos = [("female", 0.0, 5.0), ("male", 5.0, 10.0)]

    from voz.clasificador import proponer_voz

    with patch(PATCH, return_value=_mock_segmenter(segmentos)):
        resultado = proponer_voz(wav, turnos)

    assert resultado[1].etiqueta == EtiquetaVoz.INDETERMINADO


def test_limite_inferior_zona_dudosa(tmp_path: Path) -> None:
    """p_femenino exactamente 0.35 → indeterminado (límite cerrado inferior)."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav, 20.0)
    turnos = [_turno(1, 0.0, 20.0)]
    # 7 s female / 13 s male → p = 7/20 = 0.35
    segmentos = [("female", 0.0, 7.0), ("male", 7.0, 20.0)]

    from voz.clasificador import proponer_voz

    with patch(PATCH, return_value=_mock_segmenter(segmentos)):
        resultado = proponer_voz(wav, turnos)

    assert resultado[1].etiqueta == EtiquetaVoz.INDETERMINADO


def test_limite_superior_zona_dudosa(tmp_path: Path) -> None:
    """p_femenino exactamente 0.65 → indeterminado (límite cerrado superior)."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav, 20.0)
    turnos = [_turno(1, 0.0, 20.0)]
    # 13 s female / 7 s male → p = 13/20 = 0.65
    segmentos = [("female", 0.0, 13.0), ("male", 13.0, 20.0)]

    from voz.clasificador import proponer_voz

    with patch(PATCH, return_value=_mock_segmenter(segmentos)):
        resultado = proponer_voz(wav, turnos)

    assert resultado[1].etiqueta == EtiquetaVoz.INDETERMINADO


# ---------------------------------------------------------------------------
# Sin tiempo clasificable
# ---------------------------------------------------------------------------


def test_sin_tiempo_clasificable_noEnergy(tmp_path: Path) -> None:
    """Solo noEnergy → indeterminado, confianza 0.5."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav)
    turnos = [_turno(1, 0.0, 5.0)]
    segmentos = [("noEnergy", 0.0, 5.0)]

    from voz.clasificador import proponer_voz

    with patch(PATCH, return_value=_mock_segmenter(segmentos)):
        resultado = proponer_voz(wav, turnos)

    assert resultado[1].etiqueta == EtiquetaVoz.INDETERMINADO
    assert resultado[1].confianza == 0.5


# ---------------------------------------------------------------------------
# Cobertura del dict de hablantes
# ---------------------------------------------------------------------------


def test_hablante_sin_turnos_no_aparece(tmp_path: Path) -> None:
    """Hablante 2 sin turnos no aparece en el dict; hablante 1 sí."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav)
    turnos = [_turno(1, 0.0, 5.0)]
    segmentos = [("female", 0.0, 5.0)]

    from voz.clasificador import proponer_voz

    with patch(PATCH, return_value=_mock_segmenter(segmentos)):
        resultado = proponer_voz(wav, turnos)

    assert 1 in resultado
    assert 2 not in resultado


def test_todos_los_hablantes_con_turnos_aparecen(tmp_path: Path) -> None:
    """El dict contiene exactamente los hablantes con al menos un turno."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav, 10.0)
    turnos = [_turno(1, 0.0, 5.0), _turno(2, 5.0, 10.0)]
    segmentos = [("female", 0.0, 5.0), ("male", 5.0, 10.0)]

    from voz.clasificador import proponer_voz

    with patch(PATCH, return_value=_mock_segmenter(segmentos)):
        resultado = proponer_voz(wav, turnos)

    assert set(resultado.keys()) == {1, 2}


# ---------------------------------------------------------------------------
# Segmento que cruza el borde de un turno
# ---------------------------------------------------------------------------


def test_segmento_cruza_borde_de_turno(tmp_path: Path) -> None:
    """El tiempo fuera del turno de un hablante no se cuenta para él."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav, 5.0)
    # Turno [0, 3]; male [0, 2.5] → 2.5 s; female [2.5, 4.0] → solo 0.5 s (hasta 3.0)
    # p_female = 0.5/3.0 ≈ 0.1667 < 0.35 → masculino
    turnos = [_turno(1, 0.0, 3.0)]
    segmentos = [("male", 0.0, 2.5), ("female", 2.5, 4.0)]

    from voz.clasificador import proponer_voz

    with patch(PATCH, return_value=_mock_segmenter(segmentos)):
        resultado = proponer_voz(wav, turnos)

    assert resultado[1].etiqueta == EtiquetaVoz.MASCULINO
    expected = 1.0 - (0.5 / 3.0)
    assert abs(resultado[1].confianza - expected) < 1e-9


# ---------------------------------------------------------------------------
# Solapamiento entre hablantes
# ---------------------------------------------------------------------------


def test_descuenta_tiempo_compartido_entre_hablantes(tmp_path: Path) -> None:
    """El tramo donde dos hablantes se solapan no cuenta para ninguno de los dos."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav, 8.0)
    # h1: [0, 5]; h2: [3, 8] → solapamiento [3, 5]
    # Solo h1: [0, 3]; solo h2: [5, 8]
    # segmentos: female [0, 4], male [4, 8]
    # h1: female∩[0,3] = 3s, male∩[0,3] = 0s → p=1.0 → femenino
    # h2: female∩[5,8] = 0s, male∩[5,8] = 3s → p=0.0 → masculino
    turnos = [_turno(1, 0.0, 5.0), _turno(2, 3.0, 8.0)]
    segmentos = [("female", 0.0, 4.0), ("male", 4.0, 8.0)]

    from voz.clasificador import proponer_voz

    with patch(PATCH, return_value=_mock_segmenter(segmentos)):
        resultado = proponer_voz(wav, turnos)

    assert resultado[1].etiqueta == EtiquetaVoz.FEMENINO
    assert resultado[2].etiqueta == EtiquetaVoz.MASCULINO


def test_hablante_completamente_solapado_es_indeterminado(tmp_path: Path) -> None:
    """Hablante cuyos turnos se solapan completamente con otros → indeterminado, confianza 0.5."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav, 10.0)
    # h3 [3, 7] está enteramente cubierto por h1 [0, 5] y h2 [5, 10]
    turnos = [_turno(1, 0.0, 5.0), _turno(2, 5.0, 10.0), _turno(3, 3.0, 7.0)]
    segmentos = [("female", 0.0, 10.0)]

    from voz.clasificador import proponer_voz

    with patch(PATCH, return_value=_mock_segmenter(segmentos)):
        resultado = proponer_voz(wav, turnos)

    assert 3 in resultado
    assert resultado[3].etiqueta == EtiquetaVoz.INDETERMINADO
    assert resultado[3].confianza == 0.5


# ---------------------------------------------------------------------------
# El modelo se llama exactamente una vez
# ---------------------------------------------------------------------------


def test_modelo_llamado_una_sola_vez(tmp_path: Path) -> None:
    """Segmenter se instancia y llama exactamente una vez aunque haya varios hablantes."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav, 10.0)
    turnos = [_turno(1, 0.0, 5.0), _turno(2, 5.0, 10.0), _turno(3, 3.0, 7.0)]
    segmentos = [("female", 0.0, 10.0)]
    mock_seg = _mock_segmenter(segmentos)

    from voz.clasificador import proponer_voz

    with patch(PATCH, return_value=mock_seg) as mock_factory:
        proponer_voz(wav, turnos)

    mock_factory.assert_called_once()
    mock_seg.assert_called_once_with(str(wav))


# ---------------------------------------------------------------------------
# Errores
# ---------------------------------------------------------------------------


def test_paquete_ausente_lanza_excepcion_clara(tmp_path: Path) -> None:
    """Si inaSpeechSegmenter no está instalado, la excepción tiene mensaje reconocible."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav)
    turnos = [_turno(1, 0.0, 5.0)]

    from voz.clasificador import proponer_voz

    with (
        patch(PATCH, side_effect=RuntimeError("inaSpeechSegmenter no está instalado")),
        pytest.raises(RuntimeError, match="inaSpeechSegmenter"),
    ):
        proponer_voz(wav, turnos)


def test_fallo_del_modelo_lanza_excepcion_clara(tmp_path: Path) -> None:
    """Si Segmenter falla al procesar el audio, proponer_voz relanza con mensaje claro."""
    wav = tmp_path / "audio.wav"
    _crear_wav(wav)
    turnos = [_turno(1, 0.0, 5.0)]
    seg_falla = MagicMock(side_effect=RuntimeError("error interno de TensorFlow"))

    from voz.clasificador import proponer_voz

    with patch(PATCH, return_value=seg_falla), pytest.raises(RuntimeError, match="audio"):
        proponer_voz(wav, turnos)
