"""Pruebas de presencia y participación (RF-12, MD-01 a MD-06) con los 3 ejemplos y casos a mano."""

import dataclasses

import pytest
from ayudas import ESCENARIOS, cargar_ejemplo, entrada, entrada_de, senal, senales_de, turno

import contrato as c
from analisis import participacion as p
from config import CONFIG

FEM, MASC, IND = c.EtiquetaVoz.FEMENINO, c.EtiquetaVoz.MASCULINO, c.EtiquetaVoz.INDETERMINADO


# --- Los 3 ejemplos: lo calculado coincide con el resultado de ejemplo ---------------------


@pytest.fixture(params=ESCENARIOS)
def ejemplo(request):
    r = cargar_ejemplo(request.param)
    return r, entrada_de(r), senales_de(r)


def test_por_hablante_coincide_con_el_ejemplo(ejemplo):  # MD-04, MD-06
    r, e, senales = ejemplo
    filas = {f.hablante: f for f in p.por_hablante(e, senales)}
    assert set(filas) == {h.hablante for h in r.hablantes}
    for h in r.hablantes:
        f = filas[h.hablante]
        assert (f.etiqueta, f.origen) == (h.etiqueta, h.origen)
        assert f.segundos_habla == pytest.approx(h.segundos_habla, abs=1e-3)
        assert f.turnos == h.turnos
        assert f.turnos_largos == h.turnos_largos


def test_por_grupo_coincide_con_el_ejemplo(ejemplo):  # MD-02, MD-04, MD-05
    r, e, senales = ejemplo
    filas = {g.etiqueta: g for g in p.por_grupo(e, senales)}
    assert set(filas) == {g.etiqueta for g in r.grupos}
    for g in r.grupos:
        f = filas[g.etiqueta]
        assert f.numero_voces == g.numero_voces
        assert f.segundos_habla == pytest.approx(g.segundos_habla, abs=1e-3)
        assert f.turnos == g.turnos
        assert f.cuota_tiempo == pytest.approx(g.cuota_tiempo, abs=0.01)
        assert f.cuota_turnos == pytest.approx(g.cuota_turnos, abs=0.01)


def test_presencia_coincide_con_el_ejemplo(ejemplo):  # MD-01, MD-03, D-15
    r, e, senales = ejemplo
    f = p.presencia(e, senales)
    assert f.voz_femenina_presente == r.voz_femenina_presente
    assert f.primera_intervencion_femenina == r.primera_intervencion_femenina
    assert f.segundos_voces_cortas == pytest.approx(r.segundos_voces_cortas, abs=1e-3)


# --- Tiempo y turnos -----------------------------------------------------------------------


def test_el_tiempo_de_un_solapamiento_cuenta_entero_para_cada_persona():  # aclaración 1
    e = entrada([turno(1, 0.0, 10.0), turno(2, 8.0, 14.0)], {1: FEM, 2: MASC})
    segundos = {f.hablante: f.segundos_habla for f in p.por_hablante(e)}
    assert segundos == {1: 10.0, 2: 6.0}


def test_una_senal_de_escucha_no_cuenta_como_turno_pero_su_tiempo_si():  # D-14
    e = entrada(
        [turno(1, 0.0, 30.0), turno(2, 10.0, 10.5), turno(2, 40.0, 60.0)], {1: FEM, 2: MASC}
    )
    fila = {f.hablante: f for f in p.por_hablante(e, [senal(2, 1, 10.0, 10.5)])}[2]
    assert fila.turnos == 1
    assert fila.segundos_habla == 20.5


def test_sin_senales_todos_los_turnos_cuentan():
    e = entrada([turno(1, 0.0, 30.0), turno(2, 10.0, 10.5)], {1: FEM, 2: MASC})
    assert {f.hablante: f.turnos for f in p.por_hablante(e)} == {1: 1, 2: 1}


def test_turno_largo_es_de_mas_de_30_s():  # MD-06: estrictamente mayor
    e = entrada([turno(1, 0.0, 30.0), turno(1, 40.0, 70.1)], {1: FEM})
    assert p.por_hablante(e)[0].turnos_largos == 1


def test_los_umbrales_salen_de_la_configuracion():  # plan, Parte 4
    e = entrada([turno(1, 0.0, 25.0)], {1: FEM})
    assert p.por_hablante(e)[0].turnos_largos == 0
    corta = dataclasses.replace(CONFIG, turno_largo_mas_de=20.0)
    assert p.por_hablante(e, config=corta)[0].turnos_largos == 1


# --- Voces cortas (D-15) -------------------------------------------------------------------


def test_una_voz_sin_etiqueta_es_una_voz_corta():  # RN-01, D-15
    e = entrada([turno(1, 0.0, 60.0), turno(3, 61.0, 65.0), turno(3, 70.0, 72.5)], {1: FEM})
    assert p.presencia(e).segundos_voces_cortas == 6.5
    assert [f.hablante for f in p.por_hablante(e)] == [1]
    assert sum(g.segundos_habla for g in p.por_grupo(e)) == 60.0


def test_sin_voces_cortas_vale_cero():
    assert p.presencia(entrada([turno(1, 0.0, 60.0)], {1: FEM})).segundos_voces_cortas == 0.0


# --- Presencia -----------------------------------------------------------------------------


@pytest.mark.parametrize(("fin", "presente"), [(9.9, False), (10.0, True)])
def test_voz_femenina_presente_pide_10_s_o_mas(fin, presente):  # MD-01, RN-01
    e = entrada([turno(1, 0.0, fin), turno(2, 20.0, 80.0)], {1: FEM, 2: MASC})
    assert p.presencia(e).voz_femenina_presente is presente


def test_sin_voces_femeninas():
    f = p.presencia(entrada([turno(1, 0.0, 60.0)], {1: MASC}))
    assert (f.voz_femenina_presente, f.primera_intervencion_femenina) == (False, None)


def test_primera_intervencion_femenina_es_el_inicio_de_su_primer_turno():  # MD-03
    e = entrada([turno(2, 0.0, 30.0), turno(1, 31.5, 60.0)], {1: FEM, 2: MASC})
    assert p.presencia(e).primera_intervencion_femenina == 31.5


def test_la_primera_intervencion_ignora_las_senales_de_escucha():  # D-14
    e = entrada([turno(2, 0.0, 30.0), turno(1, 2.0, 2.5), turno(1, 31.0, 60.0)], {1: FEM, 2: MASC})
    assert p.presencia(e, [senal(1, 2, 2.0, 2.5)]).primera_intervencion_femenina == 31.0


# --- Grupos --------------------------------------------------------------------------------


def test_sin_voces_indeterminadas_solo_hay_dos_grupos():
    e = entrada([turno(1, 0.0, 30.0), turno(2, 30.0, 60.0)], {1: FEM, 2: MASC})
    assert [g.etiqueta for g in p.por_grupo(e)] == [FEM, MASC]


def test_el_tiempo_indeterminado_se_informa_aparte_y_no_entra_en_las_cuotas():  # RN-03, RN-04
    e = entrada(
        [turno(1, 0.0, 30.0), turno(2, 30.0, 60.0), turno(3, 60.0, 100.0)],
        {1: FEM, 2: MASC, 3: IND},
    )
    f, m, i = p.por_grupo(e)
    assert [g.etiqueta for g in (f, m, i)] == [FEM, MASC, IND]
    assert (f.cuota_tiempo, m.cuota_tiempo) == (50.0, 50.0)
    assert (f.cuota_turnos, m.cuota_turnos) == (50.0, 50.0)
    assert (i.segundos_habla, i.numero_voces, i.cuota_tiempo, i.cuota_turnos) == (
        40.0,
        1,
        None,
        None,
    )


def test_un_grupo_sin_voces_tiene_cero_voces_y_cero_segundos():  # RN-13
    f, m = p.por_grupo(entrada([turno(1, 0.0, 60.0)], {1: MASC}))
    assert (f.numero_voces, f.segundos_habla, f.turnos) == (0, 0.0, 0)
    assert (f.cuota_tiempo, m.cuota_tiempo) == (0.0, 100.0)


def test_si_no_hay_tiempo_femenino_ni_masculino_las_cuotas_no_se_aplican():  # RN-13
    f, m, i = p.por_grupo(entrada([turno(1, 0.0, 60.0)], {1: IND}))
    assert (f.cuota_tiempo, f.cuota_turnos, m.cuota_tiempo, m.cuota_turnos) == (None,) * 4
    assert i.segundos_habla == 60.0
