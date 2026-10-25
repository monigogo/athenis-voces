"""Convierte un audio de entrada a WAV mono a 16 kHz (RF-03).

Firma del contrato: contracts/pipeline-pasos.md
"""

import subprocess
import wave
from pathlib import Path

from config import CONFIG

TIEMPO_MAXIMO_SEGUNDOS = 300


def preparar(audio: Path, destino: Path) -> float:
    """Convierte `audio` a WAV mono 16 kHz y lo escribe en `destino`.

    Returns:
        Duración en segundos del WAV resultante.

    Raises:
        FileNotFoundError: si ffmpeg no está instalado.
        RuntimeError: si ffmpeg falla o el directorio de destino no existe.
        subprocess.TimeoutExpired: si la conversión supera el tiempo límite.
    """
    if not destino.parent.exists():
        raise RuntimeError(f"El directorio de destino no existe: {destino.parent}")

    cmd = [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-i", f"file:{audio}",
        "-vn",
        "-ac", "1",
        "-ar", str(CONFIG.frecuencia_muestreo),
        "-f", "wav",
        "-c:a", "pcm_s16le",
        str(destino),
    ]

    try:
        resultado = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            timeout=TIEMPO_MAXIMO_SEGUNDOS,
        )
    except subprocess.TimeoutExpired:
        destino.unlink(missing_ok=True)
        raise

    if resultado.returncode != 0:
        destino.unlink(missing_ok=True)
        stderr_lineas = resultado.stderr.decode(errors="replace").splitlines()
        stderr_recortado = "\n".join(stderr_lineas[-5:])
        raise RuntimeError(
            f"ffmpeg falló (código {resultado.returncode}):\n{stderr_recortado}"
        )

    with wave.open(str(destino)) as wf:
        duracion = wf.getnframes() / wf.getframerate()

    return duracion
