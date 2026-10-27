"""Cola del servidor: lanza las dos fases de pipeline.py, una tras otra, en un solo trabajador.

Hay una sola GPU, así que se analiza de uno en uno; mientras tanto, el análisis está «en cola».
La API sigue respondiendo porque el trabajo no corre en el hilo de las peticiones.

«Esperando confirmación» y «terminado» se publican después de guardar lo que deja cada fase: quien
vea el estado puede pedir ya los hablantes o el resultado. Un fallo inesperado acaba en «error»,
nunca colgado (RNF-16).
"""

import logging
from concurrent.futures import Executor, ThreadPoolExecutor
from pathlib import Path

from api.registro import Registro
from contrato import Confirmacion, Estado, EstadoAnalisis
from pipeline import Pasos, analizar_confirmado, preparar_para_confirmar

logger = logging.getLogger(__name__)
_AL_FINAL = {Estado.ESPERANDO_CONFIRMACION, Estado.TERMINADO}
FALLO_INTERNO = "Error interno del servidor; vuelve a intentarlo más tarde."


class Cola:
    def __init__(
        self, registro: Registro, pasos: Pasos, carpeta: Path, ejecutor: Executor | None = None
    ) -> None:
        self._registro = registro
        self._pasos = pasos
        self._carpeta = carpeta
        self._ejecutor = ejecutor or ThreadPoolExecutor(max_workers=1, thread_name_prefix="cola")

    def fase1(self, id_analisis: str) -> None:
        self._ejecutor.submit(self._con_red, id_analisis, self._preparar)

    def fase2(self, id_analisis: str, confirmacion: Confirmacion) -> None:
        self._ejecutor.submit(self._con_red, id_analisis, self._analizar, confirmacion)

    def _con_red(self, id_analisis, fase, *argumentos) -> None:
        aplazado: list[EstadoAnalisis] = []

        def notificar(estado: EstadoAnalisis) -> None:
            if estado.estado in _AL_FINAL:
                aplazado.append(estado)
            else:
                self._registro.notificar(estado)

        try:
            fase(id_analisis, notificar, *argumentos)
        except Exception:
            logger.exception("Fallo inesperado en el análisis %s", id_analisis)
            self._registro.notificar(
                EstadoAnalisis(
                    id_analisis=id_analisis, estado=Estado.ERROR, motivo_error=FALLO_INTERNO
                )
            )
            return
        for estado in aplazado:
            self._registro.notificar(estado)

    def _preparar(self, id_analisis, notificar) -> None:
        analisis = self._registro.obtener(id_analisis)
        preparado = preparar_para_confirmar(
            id_analisis,
            analisis.audio,
            self._carpeta,
            self._pasos,
            notificar,
            modo_manual=analisis.modo_manual,
        )
        analisis.wav = self._carpeta / f"{id_analisis}.wav"  # el nombre que le da el pipeline
        analisis.preparado = preparado

    def _analizar(self, id_analisis, notificar, confirmacion: Confirmacion) -> None:
        analisis = self._registro.obtener(id_analisis)
        analisis.resultado = analizar_confirmado(
            id_analisis, analisis.preparado, confirmacion, self._pasos, notificar
        )
