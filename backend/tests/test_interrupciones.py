"""Pruebas de las interrupciones (RF-14; MD-14 a MD-17; reglas del catálogo 6.7)."""

import dataclasses

import pytest
from ayudas import ESCENARIOS, cargar_ejemplo, entrada, entrada_de, turno

import contrato as c
from analisis import interrupciones as i
from config import CONFIG

FEM, MASC = c.EtiquetaVoz.FEMENINO, c.EtiquetaVoz.MASCULINO
EXITO = c.TipoSolapamiento.CON_EXITO
INTENTO = c.TipoSolapamiento.INTENTO
SENAL = c.TipoSolapamiento.SENAL_DE_ESCUCHA


def tipos(e, config=CONFIG):
    return [(x.interrumpe, x.interrumpido, x.tipo) for x in i.detectar(e, config)]


# --- Los 3 ejemplos ------------------------------------------------------------------------


@pytest.fixture(params=ESCENARIOS)
def ejemplo(request):
    r = cargar_ejemplo(request.param)
    return r, entrada_de(r)


def test_detectar_coincide_con_el_ejemplo(ejemplo):  # RF-14
    r, e = ejemplo
    assert i.detectar(e) == r.interrupciones


def test_metricas_por_hablante_coinciden_con_el_ejemplo(ejemplo):  # MD-14 a MD-17
    r, e = ejemplo
    filas = {f.hablante: f for f in i.por_hablante(e, i.detectar(e))}
    for h in r.hablantes:
        f = filas[h.hablante]
        assert (f.recibidas, f.hechas) == (h.interrupciones_recibidas, h.interrupciones_hechas)
        assert f.tasa_recibida == pytest.approx(h.tasa_interrupcion_recibida, abs=1e-3)
        assert f.apoyos_recibidos == pytest.approx(h.apoyos_recibidos, abs=1e-3)
        if h.recupera_palabra is None:
            assert f.recupera_palabra is None
        else:
            assert f.recupera_palabra == pytest.approx(h.recupera_palabra, abs=0.01)


def test_metricas_por_grupo_coinciden_con_el_ejemplo(ejemplo):
    r, e = ejemplo
    filas = {g.etiqueta: g for g in i.por_grupo(e, i.detectar(e))}
    for g in r.grupos:
        assert filas[g.etiqueta].recibidas == g.interrupciones_recibidas
        if g.tasa_interrupcion_recibida is None:
            assert filas[g.etiqueta].tasa_recibida is None
        else:
            assert filas[g.etiqueta].tasa_recibida == pytest.approx(
                g.tasa_interrupcion_recibida, abs=1e-3
            )


# --- Cuándo hay un candidato (6.7) ---------------------------------------------------------


def test_solaparse_0_3_s_justos_no_es_candidato():  # «más de 0,3 s»
    e = entrada([turno(1, 0.0, 10.0), turno(2, 9.7, 30.0)], {1: FEM, 2: MASC})
    assert tipos(e) == []


def test_solaparse_mas_de_0_3_s_si_es_candidato():
    e = entrada([turno(1, 0.0, 10.0), turno(2, 9.6, 30.0)], {1: FEM, 2: MASC})
    assert tipos(e) == [(2, 1, EXITO)]


def test_si_empiezan_a_la_vez_nadie_interrumpe():
    e = entrada([turno(1, 0.0, 10.0), turno(2, 0.0, 20.0)], {1: FEM, 2: MASC})
    assert tipos(e) == []


def test_turnos_seguidos_sin_pisarse_no_son_candidatos():
    e = entrada([turno(1, 0.0, 10.0), turno(2, 10.0, 20.0)], {1: FEM, 2: MASC})
    assert tipos(e) == []


# --- Los tres tipos (6.7) ------------------------------------------------------------------


def test_con_exito_si_a_se_calla_en_2_s_justos():  # «en los 2 s siguientes»
    e = entrada([turno(1, 10.0, 20.0), turno(2, 18.0, 30.0)], {1: FEM, 2: MASC})
    assert tipos(e) == [(2, 1, EXITO)]


def test_intento_si_a_sigue_mas_de_2_s_y_b_habla_1_s_o_mas():
    e = entrada([turno(1, 10.0, 40.0), turno(2, 20.0, 21.0)], {1: FEM, 2: MASC})
    assert tipos(e) == [(2, 1, INTENTO)]


def test_senal_de_escucha_si_b_habla_menos_de_1_s_y_a_sigue():
    e = entrada([turno(1, 10.0, 40.0), turno(2, 20.0, 20.9)], {1: FEM, 2: MASC})
    assert tipos(e) == [(2, 1, SENAL)]


def test_el_tramo_de_la_interrupcion_es_el_solapamiento():  # para escucharla (RF-18)
    e = entrada([turno(1, 10.0, 40.0), turno(2, 20.0, 50.0)], {1: FEM, 2: MASC})
    (x,) = i.detectar(e)
    assert (x.inicio, x.fin) == (20.0, 40.0)


def test_b_interrumpe_a_todas_las_que_estan_hablando():  # «de A a B», por cada A
    e = entrada(
        [turno(1, 0.0, 40.0), turno(2, 10.0, 40.0), turno(3, 20.0, 21.0)],
        {1: FEM, 2: MASC, 3: MASC},
    )
    assert sorted(t for t in tipos(e) if t[0] == 3) == [(3, 1, INTENTO), (3, 2, INTENTO)]


def test_una_voz_corta_ni_interrumpe_ni_es_interrumpida():  # D-15
    e = entrada([turno(1, 0.0, 30.0), turno(3, 10.0, 15.0), turno(3, 29.0, 31.0)], {1: FEM})
    assert tipos(e) == []


def test_las_interrupciones_salen_por_orden_de_inicio():
    e = entrada(
        [turno(1, 0.0, 30.0), turno(2, 20.0, 50.0), turno(1, 45.0, 60.0)], {1: FEM, 2: MASC}
    )
    assert [x.inicio for x in i.detectar(e)] == [20.0, 45.0]


def test_los_umbrales_salen_de_la_configuracion():  # plan, Parte 4
    e = entrada([turno(1, 10.0, 40.0), turno(2, 20.0, 21.0)], {1: FEM, 2: MASC})
    assert tipos(e) == [(2, 1, INTENTO)]
    exigente = dataclasses.replace(CONFIG, intento_desde_segundos=2.0)
    assert tipos(e, exigente) == [(2, 1, SENAL)]


# --- Métricas por persona (MD-14 a MD-17) --------------------------------------------------


def fila(e, hablante):
    return {f.hablante: f for f in i.por_hablante(e, i.detectar(e))}[hablante]


def test_recibidas_y_hechas_no_cuentan_las_senales():  # MD-14, RN-07
    e = entrada(
        [turno(1, 0.0, 40.0), turno(2, 10.0, 10.5), turno(2, 20.0, 22.0)], {1: FEM, 2: MASC}
    )
    assert (fila(e, 1).recibidas, fila(e, 2).hechas) == (1, 1)


def test_tasa_por_cada_10_minutos_de_habla_propia():  # MD-15, RN-08
    turnos = [turno(1, 0.0, 600.0)] + [turno(2, s, s + 1.5) for s in (100.0, 200.0, 300.0)]
    e = entrada(turnos, {1: FEM, 2: MASC}, duracion=700.0)
    assert (fila(e, 1).recibidas, fila(e, 1).tasa_recibida) == (3, 3.0)


def test_apoyos_recibidos_por_cada_10_minutos():  # MD-17
    turnos = [turno(1, 0.0, 600.0)] + [turno(2, s, s + 0.5) for s in (100.0, 200.0)]
    turnos.append(turno(2, 610.0, 630.0))
    e = entrada(turnos, {1: FEM, 2: MASC}, duracion=700.0)
    assert (fila(e, 1).apoyos_recibidos, fila(e, 1).recibidas) == (2.0, 0)


@pytest.mark.parametrize(("vuelve", "porcentaje"), [(30.0, 100.0), (30.1, 0.0)])
def test_recupera_la_palabra_en_10_s_o_menos(vuelve, porcentaje):  # MD-16
    e = entrada(
        [turno(1, 0.0, 20.0), turno(2, 19.0, 29.0), turno(1, vuelve, vuelve + 20.0)],
        {1: FEM, 2: MASC},
    )
    assert fila(e, 1).recupera_palabra == porcentaje


def test_sin_interrupciones_con_exito_recibidas_no_aplica():  # RN-13
    e = entrada([turno(1, 0.0, 40.0), turno(2, 20.0, 22.0)], {1: FEM, 2: MASC})
    assert fila(e, 1).recupera_palabra is None


def test_una_senal_de_escucha_no_es_volver_a_hablar():  # D-14
    e = entrada(
        [turno(1, 0.0, 20.0), turno(2, 19.0, 40.0), turno(1, 25.0, 25.5), turno(1, 50.0, 70.0)],
        {1: FEM, 2: MASC},
    )
    assert fila(e, 1).recupera_palabra == 0.0


# --- Métricas por grupo --------------------------------------------------------------------


def test_por_grupo_suma_las_de_sus_voces():
    e = entrada(
        [turno(1, 0.0, 40.0), turno(2, 10.0, 12.0), turno(3, 20.0, 22.0)],
        {1: FEM, 2: MASC, 3: MASC},
    )
    grupos = {g.etiqueta: g for g in i.por_grupo(e, i.detectar(e))}
    assert (grupos[FEM].recibidas, grupos[MASC].recibidas) == (2, 0)
    assert grupos[FEM].tasa_recibida == 30.0  # 2 en 40 s = 30 por cada 10 min


def test_un_grupo_sin_tiempo_no_tiene_tasa():  # RN-13
    e = entrada([turno(1, 0.0, 40.0), turno(2, 20.0, 22.0)], {1: MASC, 2: MASC})
    grupos = {g.etiqueta: g for g in i.por_grupo(e, i.detectar(e))}
    assert (grupos[FEM].recibidas, grupos[FEM].tasa_recibida) == (0, None)
