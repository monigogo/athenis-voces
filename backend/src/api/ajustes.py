"""Ajustes del servidor que dependen de dónde se despliega; llegan del entorno (spec 003).

- CARPETA_TRABAJO: dónde van el audio subido y su WAV. Por defecto, una subcarpeta del directorio
  temporal del sistema, nunca el repositorio (RD-04).
- EJEMPLOS_DIR: carpeta con los Resultado en JSON de los ejemplos precalculados (RF-02).
- DEMO_PUBLICA: si está activa, no se admiten subidas (D-08) [VALIDAR].

Los umbrales (tamaño, duración, retención) no van aquí: viven en config.py.
"""

import os
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

EJEMPLOS_POR_DEFECTO = Path(__file__).resolve().parents[2] / "ejemplos"
_AFIRMATIVOS = {"1", "true", "si", "sí"}


@dataclass(frozen=True)
class Ajustes:
    carpeta_trabajo: Path
    ejemplos: Path = EJEMPLOS_POR_DEFECTO
    demo_publica: bool = False


def desde_entorno(entorno: Mapping[str, str] = os.environ) -> Ajustes:
    carpeta = entorno.get("CARPETA_TRABAJO") or Path(tempfile.gettempdir()) / "athenis-voces"
    return Ajustes(
        carpeta_trabajo=Path(carpeta),
        ejemplos=Path(entorno.get("EJEMPLOS_DIR") or EJEMPLOS_POR_DEFECTO),
        demo_publica=entorno.get("DEMO_PUBLICA", "").strip().lower() in _AFIRMATIVOS,
    )
