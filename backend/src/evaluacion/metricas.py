"""Métricas de evaluación (funcional, 12.1): M-01 a M-05 y M-08, la línea base y el bootstrap.

None significa «no aplicable» (RN-13). El remuestreo usa una semilla fija (11.4).
"""

import random
import statistics
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from contrato import EntradaAnalisis, EtiquetaVoz
from evaluacion.lectura import Anotacion, Tramo

SEMILLA = 20261024
NINGUNO = "ninguno"  # lo que marca una anotadora y la otra no (M-08)
GRUPOS = (EtiquetaVoz.FEMENINO, EtiquetaVoz.MASCULINO)

ParVoz = tuple[EtiquetaVoz, EtiquetaVoz]  # (referencia, propuesta del modelo) de un hablante


def emparejar(
    a: Sequence[float], b: Sequence[float], tolerancia: float = 1.0
) -> list[tuple[int, int]]:
    """Empareja instantes uno a uno, de los más cercanos a los más lejanos, a ± tolerancia."""
    cercanos = sorted(
        (abs(x - y), i, j)
        for i, x in enumerate(a)
        for j, y in enumerate(b)
        if round(abs(x - y), 6) <= tolerancia
    )
    usados_a, usados_b, pares = set(), set(), []
    for _, i, j in cercanos:
        if i not in usados_a and j not in usados_b:
            pares.append((i, j))
            usados_a.add(i)
            usados_b.add(j)
    return sorted(pares)


@dataclass(frozen=True)
class Deteccion:
    verdaderos: int
    falsos: int
    perdidos: int

    @property
    def precision(self) -> float | None:
        total = self.verdaderos + self.falsos
        return self.verdaderos / total if total else None

    @property
    def exhaustividad(self) -> float | None:
        total = self.verdaderos + self.perdidos
        return self.verdaderos / total if total else None

    @property
    def f1(self) -> float | None:
        # Equivale a la media armónica de precisión y exhaustividad, pero sirve también con 0
        base = 2 * self.verdaderos + self.falsos + self.perdidos
        return 2 * self.verdaderos / base if base else None


def sumar(detecciones: Sequence[Deteccion]) -> Deteccion:
    """Junta los recuentos de varios audios: la unidad es el evento (11.3)."""
    return Deteccion(
        sum(d.verdaderos for d in detecciones),
        sum(d.falsos for d in detecciones),
        sum(d.perdidos for d in detecciones),
    )


def deteccion(
    sistema: Sequence[float], referencia: Sequence[float], tolerancia: float = 1.0
) -> Deteccion:
    """M-05: compara los inicios de las interrupciones del sistema con los de la referencia."""
    verdaderos = len(emparejar(sistema, referencia, tolerancia))
    return Deteccion(verdaderos, len(sistema) - verdaderos, len(referencia) - verdaderos)


def linea_base(entrada: EntradaAnalisis) -> list[float]:
    """Línea base de 11.3: cualquier solapamiento es una interrupción, sin umbrales ni tipos."""
    etiquetadas = {e.hablante for e in entrada.etiquetas}
    turnos = [t for t in entrada.turnos if t.hablante in etiquetadas]
    return sorted(
        b.inicio
        for b in turnos
        for a in turnos
        if a.hablante != b.hablante and a.inicio < b.inicio < a.fin
    )


def kappa(a: Sequence[str], b: Sequence[str]) -> float | None:
    """Kappa de Cohen. None si no se puede calcular (sin casos, o todo en una categoría)."""
    n = len(a)
    if n == 0:
        return None
    acuerdo = sum(x == y for x, y in zip(a, b, strict=True)) / n
    azar = sum((list(a).count(k) / n) * (list(b).count(k) / n) for k in set(a) | set(b))
    if azar == 1:
        return None
    return (acuerdo - azar) / (1 - azar)


def pares_de_anotadoras(
    a: Sequence[Anotacion], b: Sequence[Anotacion], tolerancia: float = 1.0
) -> list[tuple[str, str]]:
    """Tipo que puso cada anotadora a cada evento; «ninguno» si solo lo marcó la otra."""
    pares = emparejar([x.inicio for x in a], [x.inicio for x in b], tolerancia)
    en_a, en_b = {i for i, _ in pares}, {j for _, j in pares}
    resultado = [(a[i].tipo, b[j].tipo) for i, j in pares]
    resultado += [(x.tipo, NINGUNO) for i, x in enumerate(a) if i not in en_a]
    resultado += [(NINGUNO, x.tipo) for j, x in enumerate(b) if j not in en_b]
    return resultado


def kappa_entre_anotadoras(
    a: Sequence[Anotacion], b: Sequence[Anotacion], tolerancia: float = 1.0
) -> float | None:
    """M-08."""
    pares = pares_de_anotadoras(a, b, tolerancia)
    if not pares:
        return None
    de_a, de_b = zip(*pares, strict=True)
    return kappa(de_a, de_b)


@dataclass(frozen=True)
class Der:
    """M-01: segundos con error (falsa alarma, voz perdida o confusión) sobre segundos de voz."""

    error: float
    total: float

    @property
    def valor(self) -> float | None:
        return self.error / self.total if self.total else None


def der(referencia: Sequence[Tramo], sistema: Sequence[Tramo]) -> Der:
    """M-01 con pyannote.metrics, estricto: sin margen en los bordes y con los solapamientos."""
    from pyannote.core import Annotation, Segment, Timeline
    from pyannote.metrics.diarization import DiarizationErrorRate

    def anotacion(tramos: Sequence[Tramo]) -> Annotation:
        a = Annotation()
        for k, (codigo, inicio, fin) in enumerate(tramos):
            a[Segment(inicio, fin), k] = codigo
        return a

    ref = anotacion(referencia)
    zona = Timeline([Segment(min(i for _, i, _ in referencia), max(f for _, _, f in referencia))])
    detalle = DiarizationErrorRate(collar=0.0, skip_overlap=False)(
        ref, anotacion(sistema), uem=zona, detailed=True
    )
    error = detalle["false alarm"] + detalle["missed detection"] + detalle["confusion"]
    return Der(round(error, 6), round(detalle["total"], 6))


def der_conjunto(ders: Sequence[Der]) -> Der:
    """DER de varias reuniones: suma de errores entre suma de tiempos, como pyannote.metrics."""
    return Der(sum(d.error for d in ders), sum(d.total for d in ders))


def error_porcentaje_femenino(referencia: float | None, sistema: float | None) -> float | None:
    """M-04: error absoluto, en puntos, del % de tiempo femenino."""
    if referencia is None or sistema is None:
        return None
    return round(abs(sistema - referencia), 2)


def intervalo_bootstrap(
    valores: Sequence,
    remuestreos: int = 1000,
    nivel: float = 0.95,
    semilla: int = SEMILLA,
    estadistico: Callable[[list], float | None] = statistics.fmean,
) -> tuple[float, float] | None:
    """Intervalo de confianza del 95 % por remuestreo (11.3), redondeado a 4 decimales.

    Por defecto, de la media. Con otro estadístico se remuestrean unidades enteras (por ejemplo,
    reuniones) y se recalcula la métrica con cada muestra; las muestras en las que la métrica no se
    aplica (None) no cuentan.
    """
    if not valores:
        return None
    azar = random.Random(semilla)
    muestras = (estadistico(azar.choices(valores, k=len(valores))) for _ in range(remuestreos))
    medias = sorted(x for x in muestras if x is not None)
    if not medias:
        return None
    bajo = medias[int((1 - nivel) / 2 * len(medias))]
    alto = medias[int((1 + nivel) / 2 * len(medias)) - 1]
    return round(bajo, 4), round(alto, 4)


# --- M-02 y M-03: propuesta de voz, por hablante ------------------------------------------------
# «Indeterminado» frente a una referencia femenina o masculina cuenta como fallo (anexo C, D-19).


def error_de_grupo(pares: Sequence[ParVoz], grupo: EtiquetaVoz) -> float | None:
    """M-03: parte de las voces del grupo cuya propuesta no es la de su grupo."""
    del_grupo = [propuesta for referencia, propuesta in pares if referencia is grupo]
    if not del_grupo:
        return None
    return sum(propuesta is not grupo for propuesta in del_grupo) / len(del_grupo)


def exactitud_equilibrada(pares: Sequence[ParVoz]) -> float | None:
    """M-02: media del acierto de cada grupo presente en la referencia."""
    errores = [e for g in GRUPOS if (e := error_de_grupo(pares, g)) is not None]
    return 1 - statistics.fmean(errores) if errores else None


def diferencia_entre_grupos(pares: Sequence[ParVoz]) -> float | None:
    """M-03: diferencia de error entre los dos grupos, en puntos porcentuales (RNF-06)."""
    errores = [error_de_grupo(pares, g) for g in GRUPOS]
    if None in errores:
        return None
    return abs(errores[0] - errores[1]) * 100
