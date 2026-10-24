"""Pruebas de los ejemplos de resultado: los tres escenarios del contrato (plan, Parte 12).

Cada prueba recalcula una cifra con las definiciones del funcional (6.7 y las reglas de negocio) y
la compara con el JSON. Así, un ejemplo mal calculado falla aquí y no en la web.

Criterios aclarados el 2026-10-24 (spec 002): el tiempo de un solapamiento cuenta entero para cada
persona, las señales de escucha no cuentan como turno (D-14) y los 2 s de «con éxito» se cuentan
desde que B empieza a hablar.
"""

from pathlib import Path

import pytest

import contrato as c

CARPETA = Path(__file__).parent / "ejemplos"
ESCENARIOS = ["con_voces_femeninas", "sin_voces_femeninas", "muchas_interrupciones"]
DIEZ_MINUTOS = 600.0
FEM, MASC = c.EtiquetaVoz.FEMENINO, c.EtiquetaVoz.MASCULINO


def cargar(nombre):
    texto = (CARPETA / f"{nombre}.json").read_text(encoding="utf-8")
    return c.Resultado.model_validate_json(texto)


@pytest.fixture(params=ESCENARIOS)
def r(request):
    return cargar(request.param)


def duracion(tramo):
    return tramo.fin - tramo.inicio


def candidatos(r):
    """Pares (A, B): B empieza mientras A habla y se pisan más de 0,3 s (6.7)."""
    return [
        (a, b)
        for b in r.turnos
        for a in r.turnos
        if a.hablante != b.hablante
        and a.inicio < b.inicio < a.fin
        and min(a.fin, b.fin) - b.inicio > 0.3
    ]


def tipo_segun_reglas(a, b):
    if a.fin - b.inicio <= 2.0 + 1e-9:
        return c.TipoSolapamiento.CON_EXITO
    if duracion(b) >= 1.0:
        return c.TipoSolapamiento.INTENTO
    return c.TipoSolapamiento.SENAL_DE_ESCUCHA


def cuentan(r):
    return [i for i in r.interrupciones if i.tipo.cuenta_como_interrupcion]


def grupo(r, etiqueta):
    return next(g for g in r.grupos if g.etiqueta == etiqueta)


def indice(r, nombre):
    return next(i for i in r.indices if i.nombre == nombre)


def segundos_de(r, etiqueta):
    return sum(h.segundos_habla for h in r.hablantes if h.etiqueta == etiqueta)


# --- Formato -----------------------------------------------------------------------------


def test_ejemplo_valido_y_de_ida_y_vuelta(r):
    assert c.Resultado.model_validate_json(r.model_dump_json()) == r


def test_ids_de_analisis_distintos():
    ids = [cargar(n).id_analisis for n in ESCENARIOS]
    assert len(set(ids)) == len(ids)


def test_hablantes_coinciden_con_los_turnos(r):
    assert {h.hablante for h in r.hablantes} == {t.hablante for t in r.turnos}


def test_todos_los_hablantes_son_presentes(r):  # RN-01: 10 s o más
    assert all(h.segundos_habla >= 10 for h in r.hablantes)


# --- Tiempos, solapamientos e interrupciones ---------------------------------------------


def test_tiempo_de_habla_es_la_suma_de_los_turnos(r):  # aclaración 1: cuenta entero a cada una
    for h in r.hablantes:
        suma = sum(duracion(t) for t in r.turnos if t.hablante == h.hablante)
        assert h.segundos_habla == pytest.approx(suma, abs=1e-3)


def test_solapamientos_son_todos_los_tramos_pisados(r):
    esperados = set()
    for i, a in enumerate(r.turnos):
        for b in r.turnos[i + 1 :]:
            inicio, fin = max(a.inicio, b.inicio), min(a.fin, b.fin)
            if a.hablante != b.hablante and fin > inicio:
                esperados.add(
                    (tuple(sorted((a.hablante, b.hablante))), round(inicio, 3), round(fin, 3))
                )
    reales = {
        (tuple(sorted(s.hablantes)), round(s.inicio, 3), round(s.fin, 3)) for s in r.solapamientos
    }
    assert reales == esperados


def test_interrupciones_son_los_candidatos_clasificados_por_las_reglas(r):  # 6.7
    esperadas = {
        (
            b.hablante,
            a.hablante,
            tipo_segun_reglas(a, b),
            round(b.inicio, 3),
            round(min(a.fin, b.fin), 3),
        )
        for a, b in candidatos(r)
    }
    reales = {
        (i.interrumpe, i.interrumpido, i.tipo, round(i.inicio, 3), round(i.fin, 3))
        for i in r.interrupciones
    }
    assert reales == esperadas
    assert len(r.interrupciones) == len(esperadas)


def test_conteo_de_interrupciones_por_hablante(r):  # MD-14, RN-07
    for h in r.hablantes:
        assert h.interrupciones_recibidas == sum(i.interrumpido == h.hablante for i in cuentan(r))
        assert h.interrupciones_hechas == sum(i.interrumpe == h.hablante for i in cuentan(r))


def test_senales_de_escucha_no_cuentan_como_turno(r):  # D-14
    senales = [i for i in r.interrupciones if i.tipo is c.TipoSolapamiento.SENAL_DE_ESCUCHA]
    for h in r.hablantes:
        propios = sum(t.hablante == h.hablante for t in r.turnos)
        assert h.turnos == propios - sum(s.interrumpe == h.hablante for s in senales)


def test_turnos_largos_son_los_de_mas_de_30_s(r):  # MD-06
    for h in r.hablantes:
        largos = sum(duracion(t) > 30 for t in r.turnos if t.hablante == h.hablante)
        assert h.turnos_largos == largos


def test_abre_y_cierra(r):  # MD-07, MD-08: turnos de más de 5 s
    largos = sorted((t for t in r.turnos if duracion(t) > 5), key=lambda t: t.inicio)
    assert {h.hablante for h in r.hablantes if h.abre} == {largos[0].hablante}
    assert {h.hablante for h in r.hablantes if h.cierra} == {largos[-1].hablante}


def test_tasas_por_cada_10_minutos(r):  # MD-15, MD-17, RN-08
    senales = [i for i in r.interrupciones if i.tipo is c.TipoSolapamiento.SENAL_DE_ESCUCHA]
    for h in r.hablantes:
        por_10_min = h.segundos_habla / DIEZ_MINUTOS
        assert h.tasa_interrupcion_recibida == pytest.approx(
            h.interrupciones_recibidas / por_10_min, abs=1e-3
        )
        recibidas = sum(s.interrumpido == h.hablante for s in senales)
        assert h.apoyos_recibidos == pytest.approx(recibidas / por_10_min, abs=1e-3)


def test_recupera_la_palabra(r):  # MD-16: vuelve a hablar en 10 s o menos
    for h in r.hablantes:
        exitos = [
            a
            for a, b in candidatos(r)
            if a.hablante == h.hablante and tipo_segun_reglas(a, b) is c.TipoSolapamiento.CON_EXITO
        ]
        vuelve = [
            any(0 <= t.inicio - a.fin <= 10 + 1e-9 for t in r.turnos if t.hablante == h.hablante)
            for a in exitos
        ]
        if not exitos:
            assert h.recupera_palabra is None
        else:
            assert h.recupera_palabra == pytest.approx(100 * sum(vuelve) / len(exitos), abs=0.01)


# --- Grupos e índices --------------------------------------------------------------------


def test_grupos_suman_a_sus_hablantes(r):
    for g in r.grupos:
        propios = [h for h in r.hablantes if h.etiqueta == g.etiqueta]
        assert g.numero_voces == len(propios)
        assert g.segundos_habla == pytest.approx(sum(h.segundos_habla for h in propios), abs=1e-3)
        assert g.turnos == sum(h.turnos for h in propios)
        assert g.interrupciones_recibidas == sum(h.interrupciones_recibidas for h in propios)


def test_cuotas_sobre_el_tiempo_y_los_turnos_etiquetados(r):  # MD-04, MD-05, RN-04
    tiempo = sum(g.segundos_habla for g in r.grupos)
    turnos = sum(g.turnos for g in r.grupos)
    for g in r.grupos:
        assert g.cuota_tiempo == pytest.approx(100 * g.segundos_habla / tiempo, abs=0.01)
        assert g.cuota_turnos == pytest.approx(100 * g.turnos / turnos, abs=0.01)


def test_tasa_de_interrupcion_de_grupo(r):
    for g in r.grupos:
        if g.segundos_habla == 0:
            assert g.tasa_interrupcion_recibida is None
        else:
            esperada = g.interrupciones_recibidas / (g.segundos_habla / DIEZ_MINUTOS)
            assert g.tasa_interrupcion_recibida == pytest.approx(esperada, abs=1e-3)


def test_ratio_de_representacion(r):  # RR = (T_F / T_E) / (N_F / N_E)
    f, m = grupo(r, FEM), grupo(r, MASC)
    t_e, n_e = f.segundos_habla + m.segundos_habla, f.numero_voces + m.numero_voces
    valor = indice(r, c.NombreIndice.RATIO_REPRESENTACION).valor
    if f.numero_voces == 0 or t_e == 0:
        assert valor is None
    else:
        assert valor == pytest.approx((f.segundos_habla / t_e) / (f.numero_voces / n_e), abs=1e-3)


def test_brecha_de_interrupcion(r):  # BI = (I_F / (T_F / 600)) / (I_M / (T_M / 600))
    f, m = grupo(r, FEM), grupo(r, MASC)
    valor = indice(r, c.NombreIndice.BRECHA_INTERRUPCION).valor
    if f.segundos_habla == 0 or m.segundos_habla == 0 or m.interrupciones_recibidas == 0:
        assert valor is None
    else:
        tasa_f = f.interrupciones_recibidas / (f.segundos_habla / DIEZ_MINUTOS)
        tasa_m = m.interrupciones_recibidas / (m.segundos_habla / DIEZ_MINUTOS)
        assert valor == pytest.approx(tasa_f / tasa_m, abs=1e-3)


def test_los_indices_llevan_su_formula(r):  # RN-06
    assert all(i.formula for i in r.indices)
    assert {i.nombre for i in r.indices} == set(c.NombreIndice)


def test_indice_de_protagonismo(r):  # IP = 100 (0,5 P + 0,25 O + 0,25 L)
    mayor_tiempo = max(h.segundos_habla for h in r.hablantes)
    mas_largos = max(h.turnos_largos for h in r.hablantes)
    for h in r.hablantes:
        p = h.segundos_habla / mayor_tiempo
        o = (h.abre + h.cierra) / 2
        largos = h.turnos_largos / mas_largos if mas_largos else 0
        esperado = 100 * (0.5 * p + 0.25 * o + 0.25 * largos)
        assert h.indice_protagonismo == pytest.approx(esperado, abs=0.01)


# --- Lo que cada escenario tiene que enseñar ---------------------------------------------


def test_con_voces_femeninas():
    r = cargar("con_voces_femeninas")
    assert r.voz_femenina_presente
    assert r.primera_intervencion_femenina == 0.0
    assert all(i.valor is not None for i in r.indices)
    assert {i.tipo for i in r.interrupciones} == set(c.TipoSolapamiento)


def test_sin_voces_femeninas():  # RN-13
    r = cargar("sin_voces_femeninas")
    assert not r.voz_femenina_presente
    assert r.primera_intervencion_femenina is None
    assert grupo(r, FEM).numero_voces == 0
    assert all(i.valor is None for i in r.indices)


def test_muchas_interrupciones():
    r = cargar("muchas_interrupciones")
    assert len(cuentan(r)) >= 10
    assert {i.tipo for i in r.interrupciones} == set(c.TipoSolapamiento)
    assert grupo(r, FEM).numero_voces > 0 and grupo(r, MASC).numero_voces > 0
    assert all(i.valor is not None for i in r.indices)
