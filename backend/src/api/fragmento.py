"""Recorta un tramo del WAV que deja preparar.py para escucharlo (RF-07, RF-18; 9.3).

Lee solo las muestras del tramo con el módulo wave: no lanza procesos ni guarda nada en disco.
Quien llama comprueba antes que el tramo dura 15 s como máximo.
"""

import io
import wave
from pathlib import Path


def recortar(wav: Path, inicio: float, fin: float) -> bytes:
    with wave.open(str(wav), "rb") as origen:
        frecuencia = origen.getframerate()
        primero = int(inicio * frecuencia)
        cuantos = int(fin * frecuencia) - primero
        origen.setpos(min(primero, origen.getnframes()))
        muestras = origen.readframes(cuantos)
        parametros = origen.getparams()
    salida = io.BytesIO()
    with wave.open(salida, "wb") as destino:
        destino.setparams(parametros)
        destino.writeframes(muestras)
    return salida.getvalue()
