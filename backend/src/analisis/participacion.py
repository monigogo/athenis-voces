"""Presencia y participación (RF-12; métricas MD-01 a MD-06 del catálogo 6.7).

Criterios aclarados en la spec 002:
- El tiempo de un solapamiento cuenta entero para cada persona (aclaración 1).
- Las señales de escucha no cuentan como turno, aunque su tiempo sí cuenta (D-14).
- Las voces sin etiqueta confirmada son voces cortas (D-15, D-18): no son voces, no entran en ningún
  grupo y su tiempo se informa aparte.

Los segundos se redondean a 3 decimales y los porcentajes a 2.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from config import CONFIG, Config
from contrato import EntradaAnalisis, EtiquetaVoz, Interrupcion, OrigenEtiqueta, Turno

FEM, MASC, INDET = EtiquetaVoz.FEMENINO, EtiquetaVoz.MASCULINO, EtiquetaVoz.INDETERMINADO


@dataclass(frozen=True)
class ParticipacionHablante:
    hablante: int
    etiqueta: EtiquetaVoz
    origen: OrigenEtiqueta
    segundos_habla: float
    turnos: int  # sin las señales de escucha (D-14)
    turnos_largos: int  # MD-06


@dataclass(frozen=True)
class ParticipacionGrupo:
    etiqueta: EtiquetaVoz
    numero_voces: int  # MD-02
    segundos_habla: float
    turnos: int
    cuota_tiempo: float | None  # MD-04; None = no aplicable
    cuota_turnos: float | None  # MD-05; None = no aplicable


@dataclass(frozen=True)
class Presencia:
    voz_femenina_presente: bool  # MD-01
    primera_intervencion_femenina: float | None  # MD-03
    segundos_voces_cortas: float  # D-15


def _duracion(turno: Turno) -> float:
    return turno.fin - turno.inicio


def turnos_que_cuentan(
    entrada: EntradaAnalisis, senales: Sequence[Interrupcion] = ()
) -> list[Turno]:
    """Turnos de las voces etiquetadas sin las señales de escucha (D-14), por orden de inicio.

    Una señal de escucha es el turno de quien interrumpe (B) que empieza en el inicio de la señal.
    """
    etiquetadas = {e.hablante for e in entrada.etiquetas}
    excluidos = {(s.interrumpe, round(s.inicio, 6)) for s in senales}
    contados = [
        t
        for t in entrada.turnos
        if t.hablante in etiquetadas and (t.hablante, round(t.inicio, 6)) not in excluidos
    ]
    return sorted(contados, key=lambda t: (t.inicio, t.hablante))


def _segundos(entrada: EntradaAnalisis) -> dict[int, float]:
    """Segundos de habla de cada voz etiquetada; los solapamientos cuentan enteros."""
    segundos = {e.hablante: 0.0 for e in entrada.etiquetas}
    for turno in entrada.turnos:
        if turno.hablante in segundos:
            segundos[turno.hablante] += _duracion(turno)
    return segundos


def por_hablante(
    entrada: EntradaAnalisis, senales: Sequence[Interrupcion] = (), config: Config = CONFIG
) -> list[ParticipacionHablante]:
    segundos = _segundos(entrada)
    contados = turnos_que_cuentan(entrada, senales)
    filas = []
    for etiqueta in sorted(entrada.etiquetas, key=lambda e: e.hablante):
        propios = [t for t in contados if t.hablante == etiqueta.hablante]
        filas.append(
            ParticipacionHablante(
                hablante=etiqueta.hablante,
                etiqueta=etiqueta.etiqueta,
                origen=etiqueta.origen,
                segundos_habla=round(segundos[etiqueta.hablante], 3),
                turnos=len(propios),
                turnos_largos=sum(_duracion(t) > config.turno_largo_mas_de for t in propios),
            )
        )
    return filas


def por_grupo(
    entrada: EntradaAnalisis, senales: Sequence[Interrupcion] = (), config: Config = CONFIG
) -> list[ParticipacionGrupo]:
    """Femenino y masculino siempre; indeterminado solo si hay voces (RN-03, RN-04)."""
    segundos = _segundos(entrada)
    contados = turnos_que_cuentan(entrada, senales)
    de = {e.hablante: e.etiqueta for e in entrada.etiquetas}

    def voces(etiqueta):
        return sum(1 for e in de.values() if e is etiqueta)

    def tiempo(etiqueta):
        return sum((s for h, s in segundos.items() if de[h] is etiqueta), 0.0)

    def turnos(etiqueta):
        return sum(1 for t in contados if de[t.hablante] is etiqueta)

    tiempo_etiquetado = tiempo(FEM) + tiempo(MASC)  # RN-04: sin el tiempo indeterminado
    turnos_etiquetados = turnos(FEM) + turnos(MASC)
    grupos = []
    for etiqueta in (FEM, MASC, INDET):
        if etiqueta is INDET and voces(INDET) == 0:
            continue
        cuentan = etiqueta is not INDET
        grupos.append(
            ParticipacionGrupo(
                etiqueta=etiqueta,
                numero_voces=voces(etiqueta),
                segundos_habla=round(tiempo(etiqueta), 3),
                turnos=turnos(etiqueta),
                cuota_tiempo=(
                    round(100 * tiempo(etiqueta) / tiempo_etiquetado, 2)
                    if cuentan and tiempo_etiquetado > 0
                    else None
                ),
                cuota_turnos=(
                    round(100 * turnos(etiqueta) / turnos_etiquetados, 2)
                    if cuentan and turnos_etiquetados > 0
                    else None
                ),
            )
        )
    return grupos


def presencia(
    entrada: EntradaAnalisis, senales: Sequence[Interrupcion] = (), config: Config = CONFIG
) -> Presencia:
    segundos = _segundos(entrada)
    femeninas = {e.hablante for e in entrada.etiquetas if e.etiqueta is FEM}
    primeros = [t.inicio for t in turnos_que_cuentan(entrada, senales) if t.hablante in femeninas]
    cortas = sum((_duracion(t) for t in entrada.turnos if t.hablante not in segundos), 0.0)
    return Presencia(
        voz_femenina_presente=any(
            segundos[h] >= config.presencia_desde_segundos for h in femeninas
        ),
        primera_intervencion_femenina=min(primeros) if primeros else None,
        segundos_voces_cortas=round(cortas, 3),
    )
