"""Tests para audio/preparar.py (T005).

TDD: estos tests deben fallar antes de que exista la implementación.
"""

import shutil
import subprocess
import wave
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generar_wav_sintetico(ruta: Path, duracion_s: float = 2.0) -> None:
    """Crea un WAV mono 16 kHz con `duracion_s` segundos de silencio."""
    framerate = 16_000
    nframes = int(framerate * duracion_s)
    with wave.open(str(ruta), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16 bits
        wf.setframerate(framerate)
        wf.writeframes(b"\x00\x00" * nframes)


# ---------------------------------------------------------------------------
# SC-001 / RF-03: conversión real con ffmpeg
# ---------------------------------------------------------------------------


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg no disponible")
def test_preparar_produce_wav_mono_16k(tmp_path: Path) -> None:
    """preparar() devuelve duración ± 0,1 s y el WAV es mono a 16 kHz."""
    from audio.preparar import preparar

    origen = tmp_path / "entrada.wav"
    destino = tmp_path / "salida.wav"
    _generar_wav_sintetico(origen, duracion_s=2.0)

    duracion = preparar(origen, destino)

    assert destino.exists(), "el WAV de destino debe existir"
    with wave.open(str(destino)) as wf:
        assert wf.getnchannels() == 1, "debe ser mono"
        assert wf.getframerate() == 16_000, "debe ser 16 kHz"
        duracion_real = wf.getnframes() / wf.getframerate()

    assert abs(duracion - duracion_real) <= 0.01, "retorno debe coincidir con el WAV"
    assert abs(duracion - 2.0) <= 0.1, "duración ± 0,1 s respecto al original"


# ---------------------------------------------------------------------------
# FR-008: errores de conversión
# ---------------------------------------------------------------------------


def test_preparar_formato_no_admitido_lanza_excepcion(tmp_path: Path) -> None:
    """Formato .xyz → subprocess lanza FileNotFoundError → preparar() relanza excepción."""
    from audio.preparar import preparar

    origen = tmp_path / "audio.xyz"
    origen.write_bytes(b"datos invalidos")
    destino = tmp_path / "salida.wav"

    with (
        patch("subprocess.run", side_effect=FileNotFoundError("ffmpeg no encontrado")),
        pytest.raises(Exception, match="."),
    ):
        preparar(origen, destino)


def test_preparar_returncode_no_cero_lanza_excepcion(tmp_path: Path) -> None:
    """subprocess.run devuelve returncode != 0 → preparar() lanza excepción."""
    from audio.preparar import preparar

    origen = tmp_path / "audio.mp3"
    origen.write_bytes(b"datos invalidos")
    destino = tmp_path / "salida.wav"

    resultado_fallido = subprocess.CompletedProcess(
        args=[], returncode=1, stdout=b"", stderr=b"error de conversion"
    )
    with (
        patch("subprocess.run", return_value=resultado_fallido),
        pytest.raises(Exception, match="."),
    ):
        preparar(origen, destino)


def test_preparar_timeout_lanza_excepcion(tmp_path: Path) -> None:
    """subprocess.TimeoutExpired → preparar() lanza excepción."""
    from audio.preparar import preparar

    origen = tmp_path / "audio.mp3"
    origen.write_bytes(b"datos")
    destino = tmp_path / "salida.wav"

    with (
        patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=60),
        ),
        pytest.raises(Exception, match="."),
    ):
        preparar(origen, destino)


def test_preparar_directorio_inexistente_lanza_excepcion(tmp_path: Path) -> None:
    """Destino en directorio inexistente → preparar() lanza excepción."""
    from audio.preparar import preparar

    origen = tmp_path / "audio.wav"
    _generar_wav_sintetico(origen)
    destino = tmp_path / "no_existe" / "salida.wav"

    with pytest.raises(Exception, match="."):
        preparar(origen, destino)


# ---------------------------------------------------------------------------
# Nuevos tests (fase roja): limpieza, stderr recortado, opciones del comando
# ---------------------------------------------------------------------------


def test_preparar_fallo_borra_destino(tmp_path: Path) -> None:
    """Tras RuntimeError el archivo destino no existe."""
    from audio.preparar import preparar

    origen = tmp_path / "audio.mp3"
    origen.write_bytes(b"datos")
    destino = tmp_path / "salida.wav"
    destino.write_bytes(b"residuo")  # simula fichero parcial previo

    resultado_fallido = subprocess.CompletedProcess(
        args=[], returncode=1, stdout=b"", stderr=b"error"
    )
    with (
        patch("subprocess.run", return_value=resultado_fallido),
        pytest.raises(RuntimeError),
    ):
        preparar(origen, destino)

    assert not destino.exists(), "preparar() debe borrar el destino al fallar"


def test_preparar_timeout_borra_destino(tmp_path: Path) -> None:
    """Tras TimeoutExpired el archivo destino no existe."""
    from audio.preparar import preparar

    origen = tmp_path / "audio.mp3"
    origen.write_bytes(b"datos")
    destino = tmp_path / "salida.wav"
    destino.write_bytes(b"residuo")

    with (
        patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=60),
        ),
        pytest.raises(subprocess.TimeoutExpired),
    ):
        preparar(origen, destino)

    assert not destino.exists(), "preparar() debe borrar el destino al expirar"


def test_preparar_error_mensaje_maximo_5_lineas_stderr(tmp_path: Path) -> None:
    """El mensaje de RuntimeError contiene como mucho las últimas 5 líneas del stderr."""
    from audio.preparar import preparar

    origen = tmp_path / "audio.mp3"
    origen.write_bytes(b"datos")
    destino = tmp_path / "salida.wav"

    stderr_largo = b"\n".join(f"linea {i}".encode() for i in range(20))
    resultado_fallido = subprocess.CompletedProcess(
        args=[], returncode=1, stdout=b"", stderr=stderr_largo
    )
    with (
        patch("subprocess.run", return_value=resultado_fallido),
        pytest.raises(RuntimeError) as exc_info,
    ):
        preparar(origen, destino)

    lineas_en_mensaje = exc_info.value.args[0].count("\n") + 1
    assert lineas_en_mensaje <= 7, (
        "el mensaje no debe contener más de 5 líneas de stderr (+ cabecera)"
    )


def test_preparar_error_no_muestra_la_ruta_ni_el_nombre_del_audio(tmp_path: Path) -> None:
    """El nombre del archivo subido puede llevar el de una persona: no sale en el error (T017)."""
    from audio.preparar import preparar

    origen = tmp_path / "Reunion con Ana Garcia.mp3"
    origen.write_bytes(b"datos")
    destino = tmp_path / "salida.wav"

    stderr = f"file:{origen}: Invalid data found when processing input".encode()
    resultado_fallido = subprocess.CompletedProcess(
        args=[], returncode=1, stdout=b"", stderr=stderr
    )
    with (
        patch("subprocess.run", return_value=resultado_fallido),
        pytest.raises(RuntimeError) as exc_info,
    ):
        preparar(origen, destino)

    mensaje = str(exc_info.value)
    assert "Ana Garcia" not in mensaje
    assert str(tmp_path) not in mensaje
    assert "Invalid data found when processing input" in mensaje


def test_preparar_comando_incluye_opciones_requeridas(tmp_path: Path) -> None:
    """El comando ffmpeg incluye -nostdin, -hide_banner, -loglevel error, -vn, -f wav,
    -c:a pcm_s16le y la entrada como 'file:<ruta>'."""
    from audio.preparar import preparar

    origen = tmp_path / "audio.mp3"
    origen.write_bytes(b"datos")
    destino = tmp_path / "salida.wav"

    resultado_ok = subprocess.CompletedProcess(args=[], returncode=0, stdout=b"", stderr=b"")
    destino_wav_sintetico = tmp_path / "salida.wav"

    def _run_y_crea_wav(cmd, **_kwargs):  # type: ignore[no-untyped-def]
        _generar_wav_sintetico(destino_wav_sintetico)
        return resultado_ok

    with patch("subprocess.run", side_effect=_run_y_crea_wav) as mock_run:
        preparar(origen, destino)

    cmd = mock_run.call_args[0][0]
    cmd_str = " ".join(cmd)

    assert "-nostdin" in cmd, "falta -nostdin"
    assert "-hide_banner" in cmd, "falta -hide_banner"
    assert "-loglevel" in cmd and "error" in cmd, "falta -loglevel error"
    assert "-vn" in cmd, "falta -vn"
    assert "-f" in cmd and "wav" in cmd, "falta -f wav"
    assert "-c:a" in cmd and "pcm_s16le" in cmd, "falta -c:a pcm_s16le"
    assert f"file:{origen}" in cmd_str, "la entrada debe ser 'file:<ruta>'"
