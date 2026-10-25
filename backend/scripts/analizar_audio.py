"""Fase 1 del pipeline de evaluación: prepara el audio y diariza (T019).

Uso, desde backend/:
    uv run scripts/analizar_audio.py <audio> <carpeta_salida>

Escribe <carpeta_salida>/<nombre>.rttm, donde <nombre> es el nombre del audio
sin extensión y sin el sufijo ".Mix-Headset".

Rechaza rutas de salida dentro del repositorio (RD-04).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

# Permite ejecutar el script directamente desde backend/ sin PYTHONPATH=src
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _raiz_repositorio() -> Path | None:
    """Raíz del repositorio git activo, o None si no hay repo."""
    try:
        resultado = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(resultado.stdout.strip()).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _nombre_base(audio: Path) -> str:
    """Nombre del audio sin extensión y sin el sufijo '.Mix-Headset'."""
    return audio.stem.removesuffix(".Mix-Headset")


def _escribir_rttm(rttm: Path, nombre: str, turnos: list) -> None:
    """Escribe el fichero RTTM en formato NIST (10 columnas)."""
    lineas = []
    for turno in turnos:
        inicio = turno.inicio
        duracion = turno.fin - turno.inicio
        hablante = f"hablante_{turno.hablante}"
        lineas.append(
            f"SPEAKER {nombre} 1 {inicio:.3f} {duracion:.3f} <NA> <NA> {hablante} <NA> <NA>\n"
        )
    rttm.write_text("".join(lineas), encoding="utf-8")


def analizar(audio: Path, carpeta_salida: Path) -> Path:
    """Prepara el audio, diariza y escribe el RTTM.

    Returns:
        Ruta al fichero RTTM escrito.

    Raises:
        ValueError: si carpeta_salida está dentro del repositorio (RD-04).
    """
    raiz = _raiz_repositorio()
    if raiz is not None and carpeta_salida.resolve().is_relative_to(raiz):
        raise ValueError(
            f"La carpeta de salida '{carpeta_salida}' está dentro del repositorio "
            f"({raiz}). Usa una ruta fuera del repositorio (RD-04)."
        )

    from audio.diarizacion import diarizar
    from audio.preparar import preparar

    carpeta_salida.mkdir(parents=True, exist_ok=True)
    nombre = _nombre_base(audio)

    with tempfile.TemporaryDirectory() as tmpdir:
        wav_tmp = Path(tmpdir) / f"{nombre}.wav"
        preparar(audio, wav_tmp)
        turnos, _solapamientos = diarizar(wav_tmp)

    rttm = carpeta_salida / f"{nombre}.rttm"
    _escribir_rttm(rttm, nombre, turnos)
    return rttm


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fase 1: prepara el audio y diariza; escribe <nombre>.rttm"
    )
    parser.add_argument("audio", type=Path, help="Ruta al audio de entrada")
    parser.add_argument("carpeta_salida", type=Path, help="Carpeta donde escribir el RTTM")
    args = parser.parse_args()
    rttm = analizar(args.audio, args.carpeta_salida)
    print(f"RTTM escrito: {rttm}")


if __name__ == "__main__":
    main()
