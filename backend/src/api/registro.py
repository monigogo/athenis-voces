"""Registro en memoria de los análisis del servidor (spec 003, data-model).

Vive en un solo proceso: por eso el servidor se arranca sin --workers. Nunca sale por la API tal
cual; las rutas devuelven los tipos del contrato que guarda. El nombre original del audio subido no
se guarda en ningún campo (RNF-10, RD-04).
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock

from contrato import EstadoAnalisis, Resultado
from pipeline import Preparado


class AnalisisDesconocido(KeyError):
    """No hay ningún análisis con ese identificador."""


@dataclass
class Analisis:
    id_analisis: str
    creado_en: datetime  # de aquí cuenta la retención (RF-23)
    estado: EstadoAnalisis
    modo_manual: bool = False  # RF-08: el clasificador no se ejecuta
    audio: Path | None = None  # <CARPETA_TRABAJO>/<id>.subida
    wav: Path | None = None  # <CARPETA_TRABAJO>/<id>.wav, el que deja preparar.py
    preparado: Preparado | None = None  # lo que deja la fase 1
    resultado: Resultado | None = None  # lo único que queda tras la retención
    confirmado: bool = False  # ya llegó una confirmación válida
    caducado: bool = False  # la retención ya borró su audio
    es_ejemplo: bool = False


class Registro:
    def __init__(self) -> None:
        self._analisis: dict[str, Analisis] = {}
        self.cerrojo = Lock()

    def crear(self, analisis: Analisis) -> None:
        with self.cerrojo:
            self._analisis[analisis.id_analisis] = analisis

    def obtener(self, id_analisis: str) -> Analisis:
        with self.cerrojo:
            try:
                return self._analisis[id_analisis]
            except KeyError:
                raise AnalisisDesconocido(id_analisis) from None

    def todos(self) -> list[Analisis]:
        with self.cerrojo:
            return list(self._analisis.values())

    def notificar(self, estado: EstadoAnalisis) -> None:
        """La función notificar que recibe el pipeline: guarda el último estado."""
        self.obtener(estado.id_analisis).estado = estado
