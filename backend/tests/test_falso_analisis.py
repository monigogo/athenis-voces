"""Pruebas del falso del análisis: devuelve un resultado de ejemplo sin calcular nada (plan, B05)."""

import pytest

import contrato as c
import pipeline as p
from analisis import falso


def entrada(*etiquetas):
    """Entrada mínima: un turno por hablante y las etiquetas dadas, en orden."""
    return c.EntradaAnalisis(
        duracion=60.0,
        turnos=[c.Turno(hablante=i, inicio=20.0 * (i - 1), fin=20.0 * i) for i in (1, 2, 3)],
        solapamientos=[],
        etiquetas=[
            c.EtiquetaConfirmada(hablante=i, etiqueta=e, origen="persona")
            for i, e in enumerate(etiquetas, start=1)
        ],
    )


def test_devuelve_un_resultado_valido():
    assert isinstance(falso.analizar(entrada("femenino", "masculino")), c.Resultado)


def test_con_una_voz_femenina_devuelve_el_ejemplo_con_voces_femeninas():
    resultado = falso.analizar(entrada("femenino", "masculino"))
    assert resultado.voz_femenina_presente
    assert all(i.valor is not None for i in resultado.indices)


def test_sin_voces_femeninas_devuelve_el_ejemplo_sin_ellas():  # RN-13
    resultado = falso.analizar(entrada("masculino", "masculino", "indeterminado"))
    assert not resultado.voz_femenina_presente
    assert all(i.valor is None for i in resultado.indices)


def test_se_puede_elegir_el_escenario():
    resultado = falso.analizar(entrada("femenino", "masculino"), escenario="muchas_interrupciones")
    assert sum(i.tipo.cuenta_como_interrupcion for i in resultado.interrupciones) >= 10


def test_escenarios_disponibles():
    assert falso.escenarios() == [
        "con_voces_femeninas",
        "muchas_interrupciones",
        "sin_voces_femeninas",
    ]


@pytest.mark.parametrize("nombre", ["no_existe", "../test_contrato", ""])
def test_escenario_desconocido_o_con_ruta_se_rechaza(nombre):
    with pytest.raises(ValueError, match="Escenario desconocido"):
        falso.analizar(entrada("femenino", "masculino"), escenario=nombre)


def test_encaja_en_el_pipeline():  # el pipeline le pone el identificador (fase 2)
    hablantes = c.HablantesParaConfirmar(
        id_analisis="x",
        hablantes=[c.Hablante(hablante=i, segundos_habla=20.0, fragmentos=[]) for i in (1, 2, 3)],
    )
    preparado = p.Preparado(
        60.0, entrada("femenino", "masculino", "masculino").turnos, [], hablantes
    )
    confirmacion = c.Confirmacion(
        etiquetas=[
            {"hablante": 1, "etiqueta": "femenino", "origen": "persona"},
            {"hablante": 2, "etiqueta": "masculino", "origen": "persona"},
            {"hablante": 3, "etiqueta": "masculino", "origen": "persona"},
        ]
    )
    sin_usar = None
    pasos = p.Pasos(sin_usar, sin_usar, sin_usar, sin_usar, falso.analizar)
    estados = []
    resultado = p.analizar_confirmado("a1", preparado, confirmacion, pasos, estados.append)
    assert resultado.id_analisis == "a1"
    assert estados[-1].estado is c.Estado.TERMINADO
