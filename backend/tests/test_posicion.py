"""Pruebas de posición: quién abre y quién cierra (RF-13, MD-07 y MD-08)."""

import dataclasses

import pytest
from ayudas import ESCENARIOS, cargar_ejemplo, entrada, entrada_de, turno

import contrato as c
from analisis import posicion
from config import CONFIG

FEM, MASC = c.EtiquetaVoz.FEMENINO, c.EtiquetaVoz.MASCULINO


@pytest.mark.parametrize("nombre", ESCENARIOS)
def test_abre_y_cierra_coinciden_con_el_ejemplo(nombre):
    r = cargar_ejemplo(nombre)
    e = entrada_de(r)
    assert posicion.quien_abre(e) == next(h.hablante for h in r.hablantes if h.abre)
    assert posicion.quien_cierra(e) == next(h.hablante for h in r.hablantes if h.cierra)


def test_abre_quien_tiene_el_primer_turno_de_mas_de_5_s():  # MD-07
    e = entrada([turno(2, 0.0, 3.0), turno(1, 3.5, 20.0), turno(2, 21.0, 60.0)], {1: FEM, 2: MASC})
    assert posicion.quien_abre(e) == 1


def test_cierra_quien_tiene_el_ultimo_turno_de_mas_de_5_s():  # MD-08
    e = entrada(
        [turno(1, 0.0, 30.0), turno(2, 31.0, 40.0), turno(1, 41.0, 43.0)], {1: FEM, 2: MASC}
    )
    assert posicion.quien_cierra(e) == 2


def test_un_turno_de_exactamente_5_s_no_cuenta():  # «más de 5 s»
    e = entrada([turno(1, 0.0, 5.0), turno(2, 6.0, 11.5)], {1: FEM, 2: MASC})
    assert posicion.quien_abre(e) == 2


def test_si_ningun_turno_pasa_de_5_s_nadie_abre_ni_cierra():
    e = entrada([turno(1, 0.0, 4.0), turno(2, 5.0, 9.0)], {1: FEM, 2: MASC})
    assert (posicion.quien_abre(e), posicion.quien_cierra(e)) == (None, None)


def test_una_voz_corta_no_abre_ni_cierra():  # D-15: no es una voz
    e = entrada(
        [turno(3, 0.0, 6.0), turno(1, 10.0, 40.0), turno(2, 41.0, 90.0), turno(3, 91.0, 97.0)],
        {1: FEM, 2: MASC},
    )
    assert (posicion.quien_abre(e), posicion.quien_cierra(e)) == (1, 2)


def test_el_umbral_sale_de_la_configuracion():
    e = entrada([turno(1, 0.0, 4.0), turno(2, 5.0, 25.0)], {1: FEM, 2: MASC})
    assert posicion.quien_abre(e) == 2
    corta = dataclasses.replace(CONFIG, abre_cierra_turno_mas_de=3.0)
    assert posicion.quien_abre(e, corta) == 1
