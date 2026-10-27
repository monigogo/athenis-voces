"""Pipeline completo para evaluar, sin web ni persona (T019, T020).

Uso, desde backend/:
    uv run scripts/analizar_audio.py <audio> <carpeta_salida>

Escribe en <carpeta_salida>, donde <nombre> es el nombre del audio sin extensión y sin el sufijo
".Mix-Headset":
- <nombre>.rttm: quién habla y cuándo (para el DER).
- <nombre>.json: el Resultado del contrato. Las voces se confirman solas con la propuesta del
  modelo (origen «modelo»): es solo para medir; en la web las confirma una persona (RN-02).
- <nombre>.tiempo.json: duración del audio y segundos del proceso completo (M-09).

Si no hay voces suficientes (D-17) o un paso falla, queda el .rttm, no el .json, y se explica el
motivo por el error estándar.

Rechaza rutas de salida dentro del repositorio (RD-04).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Permite ejecutar el script directamente desde backend/ sin PYTHONPATH=src
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _raiz_repositorio() -> Path | None:
    """Raíz del repositorio en el que está este script, o None si no hay repo.

    Se mira desde la carpeta del script y no desde la actual: lanzado desde fuera, la protección de
    RD-04 dejaría escribir dentro del repositorio.
    """
    try:
        resultado = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parent,
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
    """Prepara el audio, diariza, analiza con las voces confirmadas por el modelo y escribe los ficheros.

    Returns:
        Ruta al fichero RTTM escrito. El JSON solo se escribe si el análisis llega a terminar.

    Raises:
        ValueError: si carpeta_salida está dentro del repositorio (RD-04).
    """
    raiz = _raiz_repositorio()
    if raiz is not None and carpeta_salida.resolve().is_relative_to(raiz):
        raise ValueError(
            f"La carpeta de salida '{carpeta_salida}' está dentro del repositorio "
            f"({raiz}). Usa una ruta fuera del repositorio (RD-04)."
        )

    from analisis.analizar import analizar as analizar_voces
    from audio.diarizacion import diarizar
    from audio.fragmentos import elegir_fragmentos
    from audio.preparar import preparar
    from contrato import Confirmacion, EstadoAnalisis, EtiquetaConfirmada, OrigenEtiqueta
    from evaluacion import cronometrar
    from pipeline import Pasos, analizar_confirmado, preparar_para_confirmar
    from voz.clasificador import proponer_voz

    carpeta_salida.mkdir(parents=True, exist_ok=True)
    nombre = _nombre_base(audio)
    rttm = carpeta_salida / f"{nombre}.rttm"

    def diarizar_y_guardar(wav: Path):
        turnos, solapamientos = diarizar(wav)
        _escribir_rttm(rttm, nombre, turnos)
        return turnos, solapamientos

    pasos = Pasos(
        preparar=preparar,
        diarizar=diarizar_y_guardar,
        proponer_voz=proponer_voz,
        elegir_fragmentos=elegir_fragmentos,
        analizar=analizar_voces,
    )
    estados: list[EstadoAnalisis] = []
    inicio = time.perf_counter()
    with tempfile.TemporaryDirectory() as tmpdir:
        preparado = preparar_para_confirmar(nombre, audio, Path(tmpdir), pasos, estados.append)
        if preparado is None:
            print(f"No se escribió el JSON: {estados[-1].motivo_error}", file=sys.stderr)
            return rttm
        confirmacion = Confirmacion(
            etiquetas=[
                EtiquetaConfirmada(
                    hablante=h.hablante, etiqueta=h.propuesta.etiqueta, origen=OrigenEtiqueta.MODELO
                )
                for h in preparado.hablantes.hablantes
            ]
        )
        resultado = analizar_confirmado(nombre, preparado, confirmacion, pasos, estados.append)
    if resultado is None:
        print(f"No se escribió el JSON: {estados[-1].motivo_error}", file=sys.stderr)
        return rttm

    (carpeta_salida / f"{nombre}.json").write_text(resultado.model_dump_json(), encoding="utf-8")
    cronometrar.guardar(
        carpeta_salida / f"{nombre}{cronometrar.SUFIJO}",
        duracion_audio=resultado.duracion,
        segundos=time.perf_counter() - inicio,
    )
    return rttm


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepara, diariza y analiza; escribe <nombre>.rttm y <nombre>.json"
    )
    parser.add_argument("audio", type=Path, help="Ruta al audio de entrada")
    parser.add_argument(
        "carpeta_salida", type=Path, help="Carpeta donde escribir el RTTM y el JSON"
    )
    args = parser.parse_args()
    rttm = analizar(args.audio, args.carpeta_salida)
    print(f"RTTM escrito: {rttm}")


if __name__ == "__main__":
    main()
