"""Pruebas de los umbrales: valores iniciales del funcional y valores imposibles."""

import dataclasses

import pytest

from config import CONFIG, Config


def test_valores_iniciales_del_funcional():
    assert CONFIG.presencia_desde_segundos == 10.0  # RN-01
    assert CONFIG.voces_presentes_minimas == 2  # D-17
    assert (CONFIG.zona_dudosa_min, CONFIG.zona_dudosa_max) == (0.35, 0.65)  # RF-06
    assert CONFIG.fragmentos_por_hablante == 3  # RF-07
    assert (CONFIG.fragmento_min_segundos, CONFIG.fragmento_max_segundos) == (3.0, 5.0)  # RF-07
    assert CONFIG.abre_cierra_turno_mas_de == 5.0  # MD-07, MD-08
    assert CONFIG.turno_largo_mas_de == 30.0  # MD-06
    assert CONFIG.solapamiento_mas_de == 0.3  # 6.7
    assert CONFIG.exito_en_segundos == 2.0  # 6.7
    assert CONFIG.intento_desde_segundos == 1.0  # 6.7
    assert CONFIG.recupera_en_segundos == 10.0  # MD-16
    assert CONFIG.segundos_por_tasa == 600.0  # RN-08
    assert (CONFIG.peso_participacion, CONFIG.peso_posicion, CONFIG.peso_turnos_largos) == (
        0.5,
        0.25,
        0.25,
    )  # 6.7, índice de protagonismo
    assert CONFIG.frecuencia_muestreo == 16_000  # RF-03
    assert CONFIG.tolerancia_duracion_segundos == 0.1  # RF-03
    assert CONFIG.escucha_antes_max_segundos == 1.0  # RF-18
    assert CONFIG.escucha_max_segundos == 15.0  # RF-18, 9.3


def test_no_se_puede_modificar_en_caliente():
    with pytest.raises(dataclasses.FrozenInstanceError):
        CONFIG.turno_largo_mas_de = 20.0


def test_variante_para_ajustar_con_desarrollo():  # RD-05: el original no cambia
    variante = dataclasses.replace(CONFIG, turno_largo_mas_de=20.0)
    assert variante.turno_largo_mas_de == 20.0
    assert CONFIG.turno_largo_mas_de == 30.0


@pytest.mark.parametrize(
    "cambios",
    [
        {"zona_dudosa_min": 0.7},  # mínimo por encima del máximo
        {"zona_dudosa_max": 1.2},  # probabilidad mayor que 1
        {"zona_dudosa_min": -0.1},  # probabilidad negativa
        {"fragmento_min_segundos": 6.0},  # mínimo por encima del máximo
        {"fragmentos_por_hablante": 0},
        {"voces_presentes_minimas": 0},
        {"exito_en_segundos": 0.0},
        {"segundos_por_tasa": -600.0},
        {"peso_posicion": -0.1},
        {"escucha_antes_max_segundos": 20.0},  # no cabe en el fragmento
    ],
)
def test_rechaza_valores_imposibles(cambios):
    with pytest.raises(ValueError):
        Config(**cambios)
