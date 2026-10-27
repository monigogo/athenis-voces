"""Retención: pasado el plazo se borran el audio y su WAV (RF-23, RNF-12; spec 003, US6).

El plazo es config.retencion_segundos: 24 h desde la subida [VALIDAR] (D-08). Solo queda el
Resultado, que son datos agregados y tiempos, sin audio. Los fragmentos no se guardan nunca: se
recortan al pedirlos.

También borra los ficheros de la carpeta de trabajo que no están en el registro (por ejemplo,
los de un servidor que se reinició) si son más viejos que el plazo, por su fecha de modificación.
Solo los que tienen nombre de fichero del servidor: <id>.subida o <id>.wav, con el id de 32
caracteres hexadecimales. Cualquier otro fichero de la carpeta no se toca.

Un fallo al borrar no detiene el hilo: se registra y se vuelve a intentar en la siguiente vuelta.
"""

import logging
import re
import threading
from datetime import datetime, timedelta
from pathlib import Path

from api.registro import Registro
from config import CONFIG
from contrato import Estado, EstadoAnalisis

logger = logging.getLogger(__name__)
NOMBRE_DEL_SERVIDOR = re.compile(r"[0-9a-f]{32}\.(subida|wav)")
MOTIVO = "Se cumplió el plazo de retención: el audio ya se ha borrado."
CADA_SEGUNDOS = 600  # cada 10 min mientras el servidor está en marcha


def borrar_caducados(
    registro: Registro, carpeta: Path, ahora: datetime, plazo: float = CONFIG.retencion_segundos
) -> None:
    limite = ahora - timedelta(seconds=plazo)
    conocidos = set()
    for analisis in registro.todos():
        conocidos.add(analisis.id_analisis)
        if analisis.es_ejemplo or analisis.caducado or analisis.creado_en >= limite:
            continue
        for ruta in (analisis.audio, analisis.wav):
            if ruta is not None:
                ruta.unlink(missing_ok=True)
        analisis.audio = analisis.wav = None
        analisis.caducado = True
        if analisis.estado.estado is not Estado.TERMINADO:
            analisis.estado = EstadoAnalisis(
                id_analisis=analisis.id_analisis, estado=Estado.ERROR, motivo_error=MOTIVO
            )
    if carpeta.is_dir():
        for fichero in carpeta.iterdir():
            if not NOMBRE_DEL_SERVIDOR.fullmatch(fichero.name) or fichero.stem in conocidos:
                continue
            try:
                viejo = fichero.stat().st_mtime < limite.timestamp()
            except FileNotFoundError:  # lo ha borrado otro mientras se revisaba
                continue
            if viejo and fichero.is_file():
                fichero.unlink(missing_ok=True)


def en_marcha(borrar, parar: threading.Event, cada: float = CADA_SEGUNDOS) -> threading.Thread:
    """Hilo que llama a `borrar` al empezar y cada `cada` segundos hasta que se pide parar."""

    def bucle() -> None:
        while True:
            try:
                borrar()
            except Exception:
                logger.exception("Falló el borrado de la retención; se reintenta en %s s", cada)
            if parar.wait(cada):
                return

    hilo = threading.Thread(target=bucle, name="retencion", daemon=True)
    hilo.start()
    return hilo
