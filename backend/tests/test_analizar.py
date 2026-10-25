"""Pruebas de la función que junta todo el análisis: EntradaAnalisis -> Resultado."""

import pytest
from ayudas import ESCENARIOS, cargar_ejemplo, entrada, entrada_de, turno

import contrato as c
import pipeline as p
from analisis.analizar import analizar


@pytest.mark.parametrize("nombre", ESCENARIOS)
def test_reproduce_el_resultado_de_ejemplo_completo(nombre):  # RF-12 a RF-16
    r = cargar_ejemplo(nombre)
    calculado = analizar(entrada_de(r))
    assert calculado.model_copy(update={"id_analisis": r.id_analisis}) == r


def test_las_voces_cortas_se_informan_aparte():  # D-15
    e = entrada(
        [turno(1, 0.0, 60.0), turno(2, 60.0, 120.0), turno(3, 121.0, 125.0)],
        {1: "femenino", 2: "masculino"},
    )
    r = analizar(e)
    assert r.segundos_voces_cortas == 4.0
    assert [h.hablante for h in r.hablantes] == [1, 2]


def test_el_resultado_cumple_el_contrato():
    e = entrada([turno(1, 0.0, 60.0), turno(2, 50.0, 120.0)], {1: "femenino", 2: "masculino"})
    r = analizar(e)
    assert c.Resultado.model_validate_json(r.model_dump_json()) == r


def test_sustituye_al_falso_en_el_pipeline():  # Pasos.analizar
    # B empieza en el 50 y A se calla en el 51: interrupción con éxito
    e = entrada([turno(1, 0.0, 51.0), turno(2, 50.0, 120.0)], {1: "femenino", 2: "masculino"})
    hablantes = c.HablantesParaConfirmar(
        id_analisis="x",
        hablantes=[c.Hablante(hablante=h, segundos_habla=60.0, fragmentos=[]) for h in (1, 2)],
    )
    preparado = p.Preparado(e.duracion, e.turnos, e.solapamientos, hablantes)
    confirmacion = c.Confirmacion(etiquetas=e.etiquetas)
    sin_usar = None
    pasos = p.Pasos(sin_usar, sin_usar, sin_usar, sin_usar, analizar)
    estados = []
    r = p.analizar_confirmado("a1", preparado, confirmacion, pasos, estados.append)
    assert r.id_analisis == "a1"
    assert estados[-1].estado is c.Estado.TERMINADO
    assert r.interrupciones[0].tipo is c.TipoSolapamiento.CON_EXITO
