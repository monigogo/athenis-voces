"""Pruebas de los índices (RF-16): ratio de representación, brecha de interrupción y protagonismo."""

import dataclasses

import pytest
from ayudas import ESCENARIOS, cargar_ejemplo

import contrato as c
from analisis import indices
from config import CONFIG

# --- Ratio de representación: RR = (T_F / T_E) / (N_F / N_E) --------------------------------


def test_ratio_de_representacion_calculado_a_mano():
    # 60 s de 100 con 1 voz de 2: hablan el 60 % siendo el 50 % -> 1,2
    assert indices.ratio_representacion(t_f=60.0, t_e=100.0, n_f=1, n_e=2) == 1.2


def test_ratio_1_es_hablar_en_proporcion():
    assert indices.ratio_representacion(t_f=50.0, t_e=100.0, n_f=1, n_e=2) == 1.0


@pytest.mark.parametrize(("t_e", "n_f", "n_e"), [(100.0, 0, 2), (0.0, 1, 2), (100.0, 0, 0)])
def test_ratio_no_aplicable_sin_voces_o_sin_tiempo(t_e, n_f, n_e):  # RN-13
    assert indices.ratio_representacion(t_f=0.0, t_e=t_e, n_f=n_f, n_e=n_e) is None


# --- Brecha de interrupción: BI = (I_F / (T_F / 600)) / (I_M / (T_M / 600)) --------------------


def test_brecha_calculada_a_mano():
    # 2 interrupciones en 10 min frente a 1 en 10 min -> 2,0
    assert indices.brecha_interrupcion(i_f=2, t_f=600.0, i_m=1, t_m=600.0) == 2.0


def test_brecha_corrige_por_cuanto_habla_cada_grupo():  # RN-08
    # Las mismas interrupciones, pero ellas hablan la mitad: el doble de tasa -> 2,0
    assert indices.brecha_interrupcion(i_f=1, t_f=300.0, i_m=1, t_m=600.0) == 2.0


def test_brecha_0_si_no_las_interrumpen_y_a_ellos_si():
    assert indices.brecha_interrupcion(i_f=0, t_f=600.0, i_m=1, t_m=600.0) == 0.0


@pytest.mark.parametrize(
    ("i_f", "t_f", "i_m", "t_m"),
    [(1, 0.0, 1, 600.0), (1, 600.0, 1, 0.0), (1, 600.0, 0, 600.0)],
)
def test_brecha_no_aplicable_si_un_denominador_es_0(i_f, t_f, i_m, t_m):  # RN-13
    assert indices.brecha_interrupcion(i_f=i_f, t_f=t_f, i_m=i_m, t_m=t_m) is None


def test_los_indices_llevan_su_formula():  # RN-06
    rr, bi = indices.de_grupo(t_f=60.0, t_m=40.0, n_f=1, n_m=1, i_f=1, i_m=1)
    assert rr.nombre is c.NombreIndice.RATIO_REPRESENTACION
    assert bi.nombre is c.NombreIndice.BRECHA_INTERRUPCION
    assert rr.formula == indices.FORMULA_RR and bi.formula == indices.FORMULA_BI
    assert (rr.valor, bi.valor) == (1.2, round((1 / 60) / (1 / 40), 3))


# --- Índice de protagonismo: IP = 100 (0,5 P + 0,25 O + 0,25 L) ------------------------------


def test_protagonismo_calculado_a_mano():
    ip = indices.protagonismo(
        segundos={1: 100.0, 2: 50.0}, abre=1, cierra=2, turnos_largos={1: 2, 2: 1}
    )
    # 1: P = 1, O = 0,5, L = 1 -> 87,5    2: P = 0,5, O = 0,5, L = 0,5 -> 50
    assert ip == {1: 87.5, 2: 50.0}


def test_sin_turnos_largos_el_componente_vale_0_para_todas():  # 6.7
    ip = indices.protagonismo(
        segundos={1: 100.0, 2: 100.0}, abre=None, cierra=None, turnos_largos={1: 0, 2: 0}
    )
    assert ip == {1: 50.0, 2: 50.0}


def test_los_pesos_salen_de_la_configuracion():  # para el análisis de sensibilidad (11.3)
    solo_tiempo = dataclasses.replace(
        CONFIG, peso_participacion=1.0, peso_posicion=0.0, peso_turnos_largos=0.0
    )
    ip = indices.protagonismo(
        segundos={1: 100.0, 2: 25.0},
        abre=2,
        cierra=2,
        turnos_largos={1: 0, 2: 3},
        config=solo_tiempo,
    )
    assert ip == {1: 100.0, 2: 25.0}


def test_sin_voces_no_hay_protagonismo():
    assert indices.protagonismo(segundos={}, abre=None, cierra=None, turnos_largos={}) == {}


# --- Los 3 ejemplos ------------------------------------------------------------------------


@pytest.mark.parametrize("nombre", ESCENARIOS)
def test_los_indices_coinciden_con_el_ejemplo(nombre):
    r = cargar_ejemplo(nombre)
    g = {x.etiqueta: x for x in r.grupos}
    f, m = g[c.EtiquetaVoz.FEMENINO], g[c.EtiquetaVoz.MASCULINO]
    calculados = indices.de_grupo(
        t_f=f.segundos_habla,
        t_m=m.segundos_habla,
        n_f=f.numero_voces,
        n_m=m.numero_voces,
        i_f=f.interrupciones_recibidas,
        i_m=m.interrupciones_recibidas,
    )
    assert calculados == r.indices
    ip = indices.protagonismo(
        segundos={h.hablante: h.segundos_habla for h in r.hablantes},
        abre=next(h.hablante for h in r.hablantes if h.abre),
        cierra=next(h.hablante for h in r.hablantes if h.cierra),
        turnos_largos={h.hablante: h.turnos_largos for h in r.hablantes},
    )
    assert ip == {h.hablante: h.indice_protagonismo for h in r.hablantes}
