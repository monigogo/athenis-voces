"""M-09: minutos de proceso por hora de audio (RNF-01).

analizar_audio.py guarda, junto a cada salida, <nombre>.tiempo.json con la duración del audio y los
segundos que tardó todo el proceso. evaluar.py los lee para la tabla de 12.1.
"""

import json
from pathlib import Path

SUFIJO = ".tiempo.json"


def minutos_por_hora(duracion_audio: float, segundos: float) -> float | None:
    if duracion_audio <= 0:
        return None
    return round(segundos * 60 / duracion_audio, 2)


def guardar(ruta: Path, duracion_audio: float, segundos: float) -> None:
    datos = {"duracion_audio": duracion_audio, "segundos": segundos}
    Path(ruta).write_text(json.dumps(datos), encoding="utf-8")


def leer_uno(ruta: Path) -> tuple[float, float]:
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return datos["duracion_audio"], datos["segundos"]


def leer(carpeta: Path) -> list[float]:
    """Minutos por hora de cada audio cronometrado, por orden de nombre."""
    valores = (minutos_por_hora(*leer_uno(r)) for r in sorted(Path(carpeta).glob(f"*{SUFIJO}")))
    return [v for v in valores if v is not None]
