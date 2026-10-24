"""Índices (RF-16; catálogo 6.7). None significa «no aplicable» (RN-13), nunca 0 ni un error.

- Ratio de representación: RR = (T_F / T_E) / (N_F / N_E). Vale 1 si las voces femeninas hablan
  en proporción a cuántas son; menos de 1, si hablan menos de lo que les correspondería.
- Brecha de interrupción: BI = (I_F / (T_F / 600)) / (I_M / (T_M / 600)). Más de 1 si se interrumpe
  más a las voces femeninas, ya corregido por cuánto habla cada grupo.
- Índice de protagonismo, por persona, de 0 a 100: IP = 100 (0,5 P + 0,25 O + 0,25 L). Los pesos
  están en config y son [VALIDAR].

T_E y N_E cuentan solo las voces femeninas y masculinas: el tiempo indeterminado va aparte (RN-04).
RR y BI se redondean a 3 decimales; el IP, a 2.
"""

from collections.abc import Mapping

from config import CONFIG, Config
from contrato import Indice, NombreIndice

FORMULA_RR = "RR = (T_F / T_E) / (N_F / N_E)"
FORMULA_BI = "BI = (I_F / (T_F / 600)) / (I_M / (T_M / 600))"


def ratio_representacion(t_f: float, t_e: float, n_f: int, n_e: int) -> float | None:
    if n_f == 0 or n_e == 0 or t_e == 0:
        return None
    return round((t_f / t_e) / (n_f / n_e), 3)


def brecha_interrupcion(
    i_f: int, t_f: float, i_m: int, t_m: float, config: Config = CONFIG
) -> float | None:
    if t_f == 0 or t_m == 0 or i_m == 0:
        return None
    decena = config.segundos_por_tasa
    return round((i_f / (t_f / decena)) / (i_m / (t_m / decena)), 3)


def de_grupo(
    t_f: float, t_m: float, n_f: int, n_m: int, i_f: int, i_m: int, config: Config = CONFIG
) -> list[Indice]:
    """Los dos índices de grupo (Must) con su fórmula (RN-06)."""
    return [
        Indice(
            nombre=NombreIndice.RATIO_REPRESENTACION,
            valor=ratio_representacion(t_f, t_f + t_m, n_f, n_f + n_m),
            formula=FORMULA_RR,
        ),
        Indice(
            nombre=NombreIndice.BRECHA_INTERRUPCION,
            valor=brecha_interrupcion(i_f, t_f, i_m, t_m, config),
            formula=FORMULA_BI,
        ),
    ]


def protagonismo(
    segundos: Mapping[int, float],
    abre: int | None,
    cierra: int | None,
    turnos_largos: Mapping[int, int],
    config: Config = CONFIG,
) -> dict[int, float]:
    """IP de cada persona (Should).

    P = su tiempo ÷ el de quien más habla; O = (abre + cierra) ÷ 2; L = sus turnos largos ÷ el
    máximo del episodio. Si el máximo de un componente es 0, ese componente vale 0 para todas.
    """
    if not segundos:
        return {}
    mayor = max(segundos.values())
    mas_largos = max(turnos_largos.values(), default=0)
    ip = {}
    for hablante, tiempo in segundos.items():
        p = tiempo / mayor if mayor else 0
        o = ((hablante == abre) + (hablante == cierra)) / 2
        largos = turnos_largos.get(hablante, 0) / mas_largos if mas_largos else 0
        ip[hablante] = round(
            100
            * (
                config.peso_participacion * p
                + config.peso_posicion * o
                + config.peso_turnos_largos * largos
            ),
            2,
        )
    return ip
