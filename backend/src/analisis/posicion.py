"""Posición: quién abre y quién cierra el episodio (RF-13; MD-07 y MD-08).

Abre quien tiene el primer turno de más de 5 s y cierra quien tiene el último. Solo cuentan las
voces etiquetadas: una voz corta (D-15) no es una voz y no abre ni cierra.
"""

from config import CONFIG, Config
from contrato import EntradaAnalisis, Turno


def _turnos_largos(entrada: EntradaAnalisis, config: Config) -> list[Turno]:
    etiquetadas = {e.hablante for e in entrada.etiquetas}
    largos = [
        t
        for t in entrada.turnos
        if t.hablante in etiquetadas and t.fin - t.inicio > config.abre_cierra_turno_mas_de
    ]
    return sorted(largos, key=lambda t: (t.inicio, t.hablante))


def quien_abre(entrada: EntradaAnalisis, config: Config = CONFIG) -> int | None:
    """Número del hablante que abre, o None si ningún turno pasa de 5 s."""
    largos = _turnos_largos(entrada, config)
    return largos[0].hablante if largos else None


def quien_cierra(entrada: EntradaAnalisis, config: Config = CONFIG) -> int | None:
    """Número del hablante que cierra, o None si ningún turno pasa de 5 s."""
    largos = _turnos_largos(entrada, config)
    return largos[-1].hablante if largos else None
