"""Métricas de evaluación (funcional, 12.1): M-04, M-05 y M-08, la línea base y el bootstrap.

None significa «no aplicable» (RN-13). El remuestreo usa una semilla fija (11.4).
"""

import random
import statistics
from collections.abc import Sequence
from dataclasses import dataclass

from contrato import EntradaAnalisis
from evaluacion.lectura import Anotacion

SEMILLA = 20261024
NINGUNO = "ninguno"  # lo que marca una anotadora y la otra no (M-08)


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
        p, r = self.precision, self.exhaustividad
        return 2 * p * r / (p + r) if p and r else None


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


def error_porcentaje_femenino(referencia: float | None, sistema: float | None) -> float | None:
    """M-04: error absoluto, en puntos, del % de tiempo femenino."""
    if referencia is None or sistema is None:
        return None
    return round(abs(sistema - referencia), 2)


def intervalo_bootstrap(
    valores: Sequence[float], remuestreos: int = 1000, nivel: float = 0.95, semilla: int = SEMILLA
) -> tuple[float, float] | None:
    """Intervalo de confianza de la media por remuestreo (11.3), redondeado a 4 decimales."""
    if not valores:
        return None
    azar = random.Random(semilla)
    medias = sorted(
        statistics.fmean(azar.choices(valores, k=len(valores))) for _ in range(remuestreos)
    )
    bajo = medias[int((1 - nivel) / 2 * remuestreos)]
    alto = medias[int((1 + nivel) / 2 * remuestreos) - 1]
    return round(bajo, 4), round(alto, 4)
