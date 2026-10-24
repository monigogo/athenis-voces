"""Interrupciones (RF-14; MD-14 a MD-17). Solo mira tiempos, nunca lo que se dice (D-10).

Reglas del catálogo 6.7: un cambio de A a B es candidato si B empieza a hablar mientras A habla y
se pisan más de 0,3 s. Si B empieza mientras hablan varias personas, B interrumpe a cada una.
- Con éxito: A deja de hablar en los 2 s siguientes a que B empieza (aclaración 3 de la spec 002).
- Intento: A sigue hablando y B habla 1 s o más.
- Señal de escucha: B habla menos de 1 s y A sigue. No cuenta como interrupción (RN-07).

Solo cuentan las voces etiquetadas: una voz corta no interrumpe ni es interrumpida (D-15).
Las restas de tiempos se redondean antes de compararlas con los umbrales, para que 10,0 - 9,7 dé
0,3 justo y no un poco más.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from analisis import participacion
from config import CONFIG, Config
from contrato import EntradaAnalisis, EtiquetaVoz, Interrupcion, TipoSolapamiento, Turno

CON_EXITO = TipoSolapamiento.CON_EXITO
INTENTO = TipoSolapamiento.INTENTO
SENAL = TipoSolapamiento.SENAL_DE_ESCUCHA


@dataclass(frozen=True)
class InterrupcionesHablante:
    hablante: int
    recibidas: int  # MD-14
    hechas: int  # MD-14
    tasa_recibida: float | None  # MD-15, por cada 10 min de habla propia (RN-08)
    recupera_palabra: float | None  # MD-16, %; None si no recibió ninguna con éxito
    apoyos_recibidos: float | None  # MD-17, señales de escucha por cada 10 min


@dataclass(frozen=True)
class InterrupcionesGrupo:
    etiqueta: EtiquetaVoz
    recibidas: int
    tasa_recibida: float | None  # None si el grupo no tiene tiempo de habla (RN-13)


def _r(segundos: float) -> float:
    return round(segundos, 6)


def _tipo(a: Turno, b: Turno, config: Config) -> TipoSolapamiento:
    if _r(a.fin - b.inicio) <= config.exito_en_segundos:
        return CON_EXITO
    if _r(b.fin - b.inicio) >= config.intento_desde_segundos:
        return INTENTO
    return SENAL


def detectar(entrada: EntradaAnalisis, config: Config = CONFIG) -> list[Interrupcion]:
    """Todos los candidatos clasificados, señales de escucha incluidas, por orden de inicio."""
    etiquetadas = {e.hablante for e in entrada.etiquetas}
    turnos = [t for t in entrada.turnos if t.hablante in etiquetadas]
    encontradas = []
    for b in turnos:
        for a in turnos:
            if a.hablante == b.hablante or not a.inicio < b.inicio < a.fin:
                continue
            fin = min(a.fin, b.fin)
            if _r(fin - b.inicio) <= config.solapamiento_mas_de:
                continue
            encontradas.append(
                Interrupcion(
                    interrumpe=b.hablante,
                    interrumpido=a.hablante,
                    tipo=_tipo(a, b, config),
                    inicio=b.inicio,
                    fin=round(fin, 3),
                )
            )
    return sorted(encontradas, key=lambda x: (x.inicio, x.fin, x.interrumpe, x.interrumpido))


def _recupera_palabra(
    hablante: int,
    cuentan: Sequence[Interrupcion],
    entrada: EntradaAnalisis,
    contados: Sequence[Turno],
    config: Config,
) -> float | None:
    """% de interrupciones con éxito tras las que vuelve a hablar en 10 s o menos (MD-16).

    Volver a hablar es empezar un turno que cuenta: una señal de escucha no lo es (D-14).
    """
    exitos = [x for x in cuentan if x.interrumpido == hablante and x.tipo is CON_EXITO]
    if not exitos:
        return None
    propios = [t for t in entrada.turnos if t.hablante == hablante]
    siguientes = [t.inicio for t in contados if t.hablante == hablante]
    vuelve = 0
    for x in exitos:
        callada = next((t.fin for t in propios if t.inicio < x.inicio < t.fin), None)
        if callada is None:
            raise ValueError(f"La interrupción de {x.inicio} s no cae en ningún turno")
        if any(0 <= _r(inicio - callada) <= config.recupera_en_segundos for inicio in siguientes):
            vuelve += 1
    return round(100 * vuelve / len(exitos), 2)


def por_hablante(
    entrada: EntradaAnalisis, interrupciones: Sequence[Interrupcion], config: Config = CONFIG
) -> list[InterrupcionesHablante]:
    cuentan = [x for x in interrupciones if x.tipo.cuenta_como_interrupcion]
    senales = [x for x in interrupciones if not x.tipo.cuenta_como_interrupcion]
    contados = participacion.turnos_que_cuentan(entrada, senales)
    filas = []
    for fila in participacion.por_hablante(entrada, senales, config):
        h = fila.hablante
        decenas = fila.segundos_habla / config.segundos_por_tasa
        recibidas = sum(x.interrumpido == h for x in cuentan)
        apoyos = sum(x.interrumpido == h for x in senales)
        filas.append(
            InterrupcionesHablante(
                hablante=h,
                recibidas=recibidas,
                hechas=sum(x.interrumpe == h for x in cuentan),
                tasa_recibida=round(recibidas / decenas, 3) if decenas > 0 else None,
                recupera_palabra=_recupera_palabra(h, cuentan, entrada, contados, config),
                apoyos_recibidos=round(apoyos / decenas, 3) if decenas > 0 else None,
            )
        )
    return filas


def por_grupo(
    entrada: EntradaAnalisis, interrupciones: Sequence[Interrupcion], config: Config = CONFIG
) -> list[InterrupcionesGrupo]:
    """Interrupciones recibidas por cada grupo y su tasa, ya corregida por cuánto habla."""
    senales = [x for x in interrupciones if not x.tipo.cuenta_como_interrupcion]
    filas = por_hablante(entrada, interrupciones, config)
    de = {e.hablante: e.etiqueta for e in entrada.etiquetas}
    grupos = []
    for grupo in participacion.por_grupo(entrada, senales, config):
        recibidas = sum(f.recibidas for f in filas if de[f.hablante] is grupo.etiqueta)
        decenas = grupo.segundos_habla / config.segundos_por_tasa
        grupos.append(
            InterrupcionesGrupo(
                etiqueta=grupo.etiqueta,
                recibidas=recibidas,
                tasa_recibida=round(recibidas / decenas, 3) if decenas > 0 else None,
            )
        )
    return grupos
