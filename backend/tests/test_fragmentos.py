"""Pruebas de audio/fragmentos.py (A13, T011): fragmentos para escuchar cada voz al confirmar."""

from itertools import pairwise

import pytest

import contrato as c
from audio.fragmentos import elegir_fragmentos
from config import CONFIG


def turno(hablante, inicio, fin):
    return c.Turno(hablante=hablante, inicio=inicio, fin=fin)


def solapamiento(inicio, fin, *hablantes):
    return c.Solapamiento(hablantes=sorted(hablantes), inicio=inicio, fin=fin)


# Hablante 1: cinco turnos limpios de 6 s repartidos entre los segundos 0 y 100.
LIMPIO = [turno(1, i, i + 6.0) for i in (0.0, 20.0, 45.0, 70.0, 94.0)]


def test_cada_voz_presente_tiene_al_menos_3_fragmentos_de_3_a_5_s():  # FR-006, SC-006
    (fragmentos,) = elegir_fragmentos(LIMPIO, []).values()
    assert len(fragmentos) >= CONFIG.fragmentos_por_hablante
    for f in fragmentos:
        assert CONFIG.fragmento_min_segundos <= f.fin - f.inicio <= CONFIG.fragmento_max_segundos


def test_los_fragmentos_de_una_voz_no_comparten_ni_un_segundo():  # clarificación 2026-10-24
    # dos turnos del mismo hablante que se pisan: no pueden salir fragmentos repetidos
    turnos = [*LIMPIO, turno(1, 2.0, 8.0)]
    fragmentos = sorted(elegir_fragmentos(turnos, [])[1], key=lambda f: f.inicio)
    for a, b in pairwise(fragmentos):
        assert a.fin <= b.inicio


def test_los_fragmentos_se_reparten_por_toda_la_intervencion():  # principio, mitad y final
    fragmentos = sorted(elegir_fragmentos(LIMPIO, [])[1], key=lambda f: f.inicio)
    principio, final = 0.0, 100.0  # lo que dura la intervención del hablante 1
    tercio = (final - principio) / 3
    assert fragmentos[0].inicio < principio + tercio
    assert fragmentos[-1].fin > final - tercio


def test_un_fragmento_nunca_incluye_un_solapamiento():
    turnos = [*LIMPIO, turno(2, 2.0, 30.0)]  # el 2 pisa al 1 en sus dos primeros turnos
    solapamientos = [solapamiento(2.0, 6.0, 1, 2), solapamiento(20.0, 26.0, 1, 2)]
    for f in elegir_fragmentos(turnos, solapamientos)[1]:
        for s in solapamientos:
            assert f.fin <= s.inicio or f.inicio >= s.fin


def test_sin_3_tramos_limpios_de_3_s_la_voz_no_aparece():  # D-18
    # 14 s de habla, pero solo 2 tramos de 3 s o más; el resto son tramos de 2 s
    turnos = [
        turno(3, 0.0, 4.0),
        turno(3, 10.0, 14.0),
        *(turno(3, i, i + 2.0) for i in (20, 30, 40)),
    ]
    assert elegir_fragmentos(turnos, []) == {}


def test_con_menos_de_10_s_de_habla_la_voz_no_aparece():  # RN-01
    turnos = [turno(4, i, i + 3.0) for i in (0.0, 10.0, 20.0)]  # 9 s en 3 tramos de 3 s
    assert elegir_fragmentos(turnos, []) == {}


def test_un_tramo_que_solo_es_limpio_en_parte_se_usa_si_quedan_3_s():
    # el turno de 10 s del hablante 1 está pisado los 7 primeros segundos: le quedan 3 s limpios
    turnos = [turno(1, 0.0, 10.0), turno(2, 0.0, 7.0), turno(1, 20.0, 26.0), turno(1, 40.0, 46.0)]
    solapamientos = [solapamiento(0.0, 7.0, 1, 2)]
    fragmentos = sorted(elegir_fragmentos(turnos, solapamientos)[1], key=lambda f: f.inicio)
    assert (fragmentos[0].inicio, fragmentos[0].fin) == (7.0, 10.0)


def test_es_siempre_el_mismo_resultado():  # sin azar: reproducible (11.4)
    assert elegir_fragmentos(LIMPIO, []) == elegir_fragmentos(LIMPIO, [])


@pytest.mark.parametrize("hablantes", [(1,), (1, 2)])
def test_devuelve_una_entrada_por_cada_voz_presente(hablantes):
    turnos = [
        turno(h, i + 100 * (h - 1), i + 100 * (h - 1) + 6.0) for h in hablantes for i in (0, 30, 60)
    ]
    assert sorted(elegir_fragmentos(turnos, [])) == list(hablantes)


# --- Un tramo largo puede dar varios fragmentos (decisión del equipo, 25 oct 2026) -------------


def test_un_tramo_largo_da_varios_fragmentos_si_faltan_tramos():
    # una sola intervención limpia de 16 s: caben tres fragmentos de 3 a 5 s
    fragmentos = elegir_fragmentos([turno(1, 0.0, 16.0)], [])[1]
    assert len(fragmentos) == CONFIG.fragmentos_por_hablante
    for a, b in pairwise(sorted(fragmentos, key=lambda f: f.inicio)):
        assert a.fin <= b.inicio  # ni un segundo compartido
    for f in fragmentos:
        assert 0.0 <= f.inicio and f.fin <= 16.0
        assert CONFIG.fragmento_min_segundos <= f.fin - f.inicio <= CONFIG.fragmento_max_segundos


def test_con_dos_tramos_se_reparten_los_fragmentos_entre_los_dos():
    # 16 s y 4 s limpios: dos tramos solos no bastan, pero entre los dos caben 3 o más fragmentos
    turnos = [turno(1, 0.0, 16.0), turno(1, 30.0, 34.0)]
    fragmentos = sorted(elegir_fragmentos(turnos, [])[1], key=lambda f: f.inicio)
    assert len(fragmentos) == CONFIG.fragmentos_por_hablante
    assert fragmentos[0].inicio < 16.0  # uno al principio
    assert fragmentos[-1].inicio >= 30.0  # y uno al final


def test_si_entre_todos_los_tramos_no_caben_3_fragmentos_la_voz_no_aparece():  # D-18
    # 4 s y 4 s: solo caben dos fragmentos de 3 s
    assert (
        elegir_fragmentos([turno(1, 0.0, 4.0), turno(1, 20.0, 24.0), turno(1, 40.0, 42.0)], [])
        == {}
    )


def test_con_tramos_de_sobra_no_se_parte_ninguno():
    # con 5 tramos limpios, cada fragmento sale de un tramo distinto, como antes
    tramos = [(t.inicio, t.fin) for t in LIMPIO]
    de_cual = [
        next(k for k, (i, e) in enumerate(tramos) if i <= f.inicio and f.fin <= e)
        for f in elegir_fragmentos(LIMPIO, [])[1]
    ]
    assert len(set(de_cual)) == len(de_cual) == CONFIG.fragmentos_por_hablante
