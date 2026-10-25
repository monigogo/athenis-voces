"""Une los pasos del análisis en orden y mantiene su estado (RF-04, RNF-16).

Fase 1, al subir un audio: preparar el audio, separar las voces, proponer la voz y elegir los
fragmentos. Acaba en «esperando confirmación». Fase 2, cuando una persona ha confirmado las voces
(RF-07): analizar. Acaba en «terminado». Si un paso falla, el análisis acaba en «error» con su
motivo, nunca colgado (RNF-16).

Solo pasan a confirmación las voces presentes (RN-01): 10 s o más de habla y al menos 3 fragmentos
para escucharlas (D-18). Las demás no se confirman y su tiempo cuenta como voz corta (D-15). Con
menos de dos voces presentes no hay nada que comparar y el análisis acaba en «error» (D-17).

Los pasos llegan desde fuera en Pasos: cada módulo real, o un falso en las pruebas, cumple la
misma firma. El estado se comunica con la función notificar, y quien la pase (la API) lo guarda.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from config import CONFIG, Config
from contrato import (
    Confirmacion,
    EntradaAnalisis,
    Estado,
    EstadoAnalisis,
    Fragmento,
    Hablante,
    HablantesParaConfirmar,
    PropuestaVoz,
    Resultado,
    Solapamiento,
    Turno,
)

Notificar = Callable[[EstadoAnalisis], None]

# Avance aproximado al empezar cada paso (RF-04)
_AVANCE = {
    "preparar el audio": 0.0,
    "separar las voces": 25.0,
    "proponer la voz": 50.0,
    "elegir los fragmentos": 75.0,
    "analizar": 90.0,
}


@dataclass(frozen=True)
class Pasos:
    """Firmas que deben cumplir los módulos (o sus falsos)."""

    # audio/preparar.py: audio subido y ruta del WAV que debe crear -> duración en segundos
    preparar: Callable[[Path, Path], float]
    # audio/diarizacion.py: WAV -> turnos y solapamientos
    diarizar: Callable[[Path], tuple[list[Turno], list[Solapamiento]]]
    # voz/clasificador.py: WAV y turnos -> propuesta por número de hablante
    proponer_voz: Callable[[Path, list[Turno]], dict[int, PropuestaVoz]]
    # audio/fragmentos.py: turnos y solapamientos -> fragmentos por número de hablante
    elegir_fragmentos: Callable[[list[Turno], list[Solapamiento]], dict[int, list[Fragmento]]]
    # analisis/: entrada con las etiquetas confirmadas -> resultado
    analizar: Callable[[EntradaAnalisis], Resultado]


@dataclass(frozen=True)
class Preparado:
    """Lo que deja la fase 1 para la fase 2."""

    duracion: float
    turnos: list[Turno]
    solapamientos: list[Solapamiento]
    hablantes: HablantesParaConfirmar


class ConfirmacionInvalida(ValueError):
    """La confirmación no cubre exactamente las voces presentes (RF-07)."""


class _PasoFallido(Exception):
    pass


def _procesando(id_analisis: str, paso: str) -> EstadoAnalisis:
    return EstadoAnalisis(id_analisis=id_analisis, estado=Estado.PROCESANDO, progreso=_AVANCE[paso])


def _error(id_analisis: str, motivo: str) -> EstadoAnalisis:
    return EstadoAnalisis(id_analisis=id_analisis, estado=Estado.ERROR, motivo_error=motivo)


def _ejecutar(id_analisis: str, paso: str, notificar: Notificar, funcion, *argumentos):
    notificar(_procesando(id_analisis, paso))
    try:
        return funcion(*argumentos)
    except Exception as error:
        raise _PasoFallido(f"Falló el paso «{paso}»: {error}") from error


def _segundos_por_hablante(turnos: list[Turno]) -> dict[int, float]:
    """Tiempo de habla de cada voz; el de un solapamiento cuenta entero para cada una."""
    segundos: dict[int, float] = {}
    for turno in turnos:
        segundos[turno.hablante] = segundos.get(turno.hablante, 0.0) + turno.fin - turno.inicio
    return segundos


def _pocas_voces(presentes: int, minimo: int) -> str:
    """Motivo del error de D-17, para que la persona entienda por qué no hay resultado."""
    if presentes == 0:
        detectadas = "No se ha detectado ninguna voz"
    elif presentes == 1:
        detectadas = "Solo se ha detectado una voz"
    else:
        detectadas = f"Solo se han detectado {presentes} voces"
    return f"{detectadas} que se pueda confirmar; hacen falta al menos {minimo}."


def preparar_para_confirmar(
    id_analisis: str,
    audio: Path,
    carpeta: Path,
    pasos: Pasos,
    notificar: Notificar,
    *,
    modo_manual: bool = False,
    config: Config = CONFIG,
) -> Preparado | None:
    """Fase 1. Devuelve None si un paso falla; el estado ya queda en «error»."""
    try:
        wav = carpeta / f"{id_analisis}.wav"  # nombre generado por el sistema (RNF-10)
        duracion = _ejecutar(
            id_analisis, "preparar el audio", notificar, pasos.preparar, audio, wav
        )
        turnos, solapamientos = _ejecutar(
            id_analisis, "separar las voces", notificar, pasos.diarizar, wav
        )
        propuestas = (
            {}  # modo manual: no se ejecuta ningún clasificador (RF-08)
            if modo_manual
            else _ejecutar(
                id_analisis, "proponer la voz", notificar, pasos.proponer_voz, wav, turnos
            )
        )
        fragmentos = _ejecutar(
            id_analisis,
            "elegir los fragmentos",
            notificar,
            pasos.elegir_fragmentos,
            turnos,
            solapamientos,
        )
        presentes = {
            h: s
            for h, s in sorted(_segundos_por_hablante(turnos).items())
            if s >= config.presencia_desde_segundos  # RN-01
            and len(fragmentos.get(h, [])) >= config.fragmentos_por_hablante  # D-18
        }
        if len(presentes) < config.voces_presentes_minimas:  # D-17
            raise _PasoFallido(_pocas_voces(len(presentes), config.voces_presentes_minimas))
        if not modo_manual:
            sin_propuesta = [h for h in presentes if h not in propuestas]
            if sin_propuesta:
                faltan = ", ".join(f"Hablante {h}" for h in sin_propuesta)
                raise _PasoFallido(f"Falta la propuesta de voz de: {faltan}")
        hablantes = HablantesParaConfirmar(
            id_analisis=id_analisis,
            hablantes=[
                Hablante(
                    hablante=h,
                    segundos_habla=segundos,
                    propuesta=propuestas.get(h),
                    fragmentos=fragmentos[h],
                )
                for h, segundos in presentes.items()
            ],
        )
    except _PasoFallido as fallo:
        notificar(_error(id_analisis, str(fallo)))
        return None
    except ValidationError as error:  # datos de un paso que no cumplen el contrato
        notificar(_error(id_analisis, f"Los datos de un paso no cumplen el contrato: {error}"))
        return None

    notificar(EstadoAnalisis(id_analisis=id_analisis, estado=Estado.ESPERANDO_CONFIRMACION))
    return Preparado(duracion, turnos, solapamientos, hablantes)


def analizar_confirmado(
    id_analisis: str,
    preparado: Preparado,
    confirmacion: Confirmacion,
    pasos: Pasos,
    notificar: Notificar,
) -> Resultado | None:
    """Fase 2. Devuelve None si el análisis falla; el estado ya queda en «error».

    Lanza ConfirmacionInvalida, sin cambiar el estado, si la confirmación no cubre justo las
    voces presentes: es un error de quien confirma y no del análisis.
    """
    presentes = {h.hablante for h in preparado.hablantes.hablantes}
    confirmados = {e.hablante for e in confirmacion.etiquetas}
    if confirmados != presentes:
        raise ConfirmacionInvalida(
            f"Hay que confirmar justo las voces presentes {sorted(presentes)}; "
            f"llegaron {sorted(confirmados)}"
        )
    try:
        entrada = EntradaAnalisis(
            duracion=preparado.duracion,
            turnos=preparado.turnos,
            solapamientos=preparado.solapamientos,
            etiquetas=confirmacion.etiquetas,
        )
        resultado = _ejecutar(id_analisis, "analizar", notificar, pasos.analizar, entrada)
    except _PasoFallido as fallo:
        notificar(_error(id_analisis, str(fallo)))
        return None
    except ValidationError as error:
        notificar(_error(id_analisis, f"Los datos no cumplen el contrato: {error}"))
        return None

    notificar(EstadoAnalisis(id_analisis=id_analisis, estado=Estado.TERMINADO))
    # El análisis no conoce el identificador: lo pone el pipeline.
    return resultado.model_copy(update={"id_analisis": id_analisis})
