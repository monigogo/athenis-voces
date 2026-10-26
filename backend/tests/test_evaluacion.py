"""Pruebas de la evaluación (B12): lectura de datos y métricas M-04, M-05 y M-08 (funcional, 11 y 12.1)."""

import pytest
from ayudas import entrada, turno

import contrato as c
from evaluacion import lectura, metricas

FEM, MASC = c.EtiquetaVoz.FEMENINO, c.EtiquetaVoz.MASCULINO

RTTM = """SPEAKER IB4002 1 0.00 20.00 <NA> <NA> FIE038 <NA> <NA>
SPEAKER IB4002 1 19.50 15.50 <NA> <NA> MIO091 <NA> <NA>
SPEAKER IB4002 1 40.00 0.00 <NA> <NA> MIO091 <NA> <NA>
SPEAKER IB4002 1 41.00 4.00 <NA> <NA> FIO093 <NA> <NA>
"""


# --- Lectura de los RTTM de AMI ------------------------------------------------------------


def test_leer_rttm(tmp_path):
    ruta = tmp_path / "IB4002.rttm"
    ruta.write_text(RTTM + "ruido que no es una línea SPEAKER\n", encoding="utf-8")
    # ignora lo que no es SPEAKER y los tramos de duración 0
    assert lectura.leer_rttm(ruta) == [
        ("FIE038", 0.0, 20.0),
        ("MIO091", 19.5, 35.0),
        ("FIO093", 41.0, 45.0),
    ]


def test_entrada_de_referencia_usa_la_primera_letra_del_codigo(tmp_path):  # 11.2
    e, codigos = lectura.entrada_de_referencia(
        [("MIO091", 19.5, 35.0), ("FIE038", 0.0, 20.0), ("FIO093", 41.0, 45.0)]
    )
    assert codigos == {1: "FIE038", 2: "FIO093", 3: "MIO091"}
    etiquetas = {x.hablante: x.etiqueta for x in e.etiquetas}
    # FIO093 habla 4 s: es una voz corta y no se etiqueta (RN-01, D-15)
    assert etiquetas == {1: FEM, 3: MASC}
    assert [(s.hablantes, s.inicio, s.fin) for s in e.solapamientos] == [([1, 3], 19.5, 20.0)]
    assert e.duracion == 45.0


def test_codigo_sin_f_ni_m_se_rechaza():
    with pytest.raises(ValueError, match="XYZ001"):
        lectura.entrada_de_referencia([("XYZ001", 0.0, 20.0)])


# --- Lectura de las etiquetas de Audacity -------------------------------------------------


def test_leer_etiquetas_de_audacity(tmp_path):
    ruta = tmp_path / "grabacion1_A.txt"
    ruta.write_text(
        "12.5\t13.9\tcon_exito\n"
        "\\\t100.0\t2000.0\n"  # línea de frecuencias de Audacity: se ignora
        "20,25\t21,00\tsenal_de_escucha\n"  # coma decimal
        "30.0\t32.0\t colaborativo \n",
        encoding="utf-8",
    )
    assert lectura.leer_etiquetas(ruta) == [
        lectura.Anotacion(12.5, 13.9, "con_exito"),
        lectura.Anotacion(20.25, 21.0, "senal_de_escucha"),
        lectura.Anotacion(30.0, 32.0, "colaborativo"),
    ]


def test_etiqueta_desconocida_dice_la_linea(tmp_path):
    ruta = tmp_path / "x_C.txt"
    ruta.write_text("1.0\t2.0\tintento\n3.0\t4.0\tinterrupcion\n", encoding="utf-8")
    with pytest.raises(ValueError, match="línea 2"):
        lectura.leer_etiquetas(ruta)


def test_solo_con_exito_e_intento_cuentan():  # RN-07, D-16
    cuentan = [lectura.Anotacion(0.0, 1.0, t).cuenta for t in lectura.TIPOS_ANOTACION]
    assert dict(zip(lectura.TIPOS_ANOTACION, cuentan, strict=True)) == {
        "con_exito": True,
        "intento": True,
        "senal_de_escucha": False,
        "colaborativo": False,
    }


# --- M-05: detección con tolerancia de ± 1 s ----------------------------------------------


def test_emparejar_uno_a_uno_por_cercania():
    assert metricas.emparejar([10.0, 10.5], [10.4]) == [(1, 0)]


def test_la_tolerancia_de_1_s_incluye_el_borde():
    assert metricas.emparejar([10.0], [11.0]) == [(0, 0)]
    assert metricas.emparejar([10.0], [11.1]) == []


def test_precision_exhaustividad_y_f1_a_mano():
    d = metricas.deteccion(sistema=[10.0, 20.0, 30.0, 40.0], referencia=[10.5, 20.5, 50.0])
    assert (d.verdaderos, d.falsos, d.perdidos) == (2, 2, 1)
    assert d.precision == 0.5
    assert d.exhaustividad == pytest.approx(2 / 3)
    assert d.f1 == pytest.approx(4 / 7)


def test_sin_eventos_las_medidas_no_se_aplican():  # RN-13
    d = metricas.deteccion(sistema=[], referencia=[])
    assert (d.precision, d.exhaustividad, d.f1) == (None, None, None)


@pytest.mark.parametrize(
    ("sistema", "referencia"), [([10.0, 30.0], [50.0]), ([], [50.0]), ([10.0], [])]
)
def test_si_hay_eventos_y_no_acierta_ninguno_el_f1_es_0(sistema, referencia):
    # un 0 de verdad: no se esconde como «no aplicable»
    assert metricas.deteccion(sistema=sistema, referencia=referencia).f1 == 0.0


def test_detecciones_de_varios_audios_suman_sus_recuentos():  # unidad: el evento (11.3)
    juntas = metricas.sumar([metricas.Deteccion(1, 0, 1), metricas.Deteccion(2, 3, 0)])
    assert juntas == metricas.Deteccion(3, 3, 1)
    assert metricas.sumar([]) == metricas.Deteccion(0, 0, 0)


def test_linea_base_cuenta_cualquier_solapamiento():  # 11.3
    e = entrada(
        [turno(1, 0.0, 30.0), turno(2, 10.0, 10.2), turno(2, 20.0, 20.5), turno(2, 29.9, 40.0)],
        {1: FEM, 2: MASC},
    )
    # también los de menos de 0,3 s y las señales de escucha
    assert metricas.linea_base(e) == [10.0, 20.0, 29.9]


# --- M-08: kappa de Cohen ------------------------------------------------------------------


def test_kappa_de_un_ejemplo_conocido():
    # 50 casos: 20 sí-sí, 5 sí-no, 10 no-sí, 15 no-no -> p_o = 0,7, p_e = 0,5, kappa = 0,4
    a = ["si"] * 25 + ["no"] * 25
    b = ["si"] * 20 + ["no"] * 5 + ["si"] * 10 + ["no"] * 15
    assert metricas.kappa(a, b) == pytest.approx(0.4)


def test_kappa_acuerdo_total():
    assert metricas.kappa(["a", "b", "a"], ["a", "b", "a"]) == 1.0


def test_kappa_no_aplicable_si_todo_es_la_misma_categoria():  # 0 / 0
    assert metricas.kappa(["a", "a"], ["a", "a"]) is None


def test_kappa_entre_anotadoras_cuenta_lo_que_solo_marca_una():
    a = [lectura.Anotacion(10.0, 11.0, "intento"), lectura.Anotacion(30.0, 31.0, "con_exito")]
    b = [lectura.Anotacion(10.4, 11.0, "intento"), lectura.Anotacion(50.0, 51.0, "con_exito")]
    pares = metricas.pares_de_anotadoras(a, b)
    assert sorted(pares) == [
        ("con_exito", "ninguno"),
        ("intento", "intento"),
        ("ninguno", "con_exito"),
    ]


# --- M-04 y el intervalo de confianza ------------------------------------------------------


def test_error_absoluto_del_porcentaje_femenino():
    assert metricas.error_porcentaje_femenino(referencia=58.0, sistema=55.5) == 2.5
    assert metricas.error_porcentaje_femenino(referencia=None, sistema=55.5) is None


def test_bootstrap_es_reproducible_y_razonable():  # 11.3, 11.4: semilla fija
    valores = [0.5, 0.6, 0.7, 0.8, 0.9]
    a = metricas.intervalo_bootstrap(valores)
    assert a == metricas.intervalo_bootstrap(valores)
    assert min(valores) <= a[0] <= a[1] <= max(valores)


def test_bootstrap_de_valores_iguales():
    assert metricas.intervalo_bootstrap([0.7, 0.7, 0.7]) == (0.7, 0.7)


def test_bootstrap_sin_valores_no_se_aplica():
    assert metricas.intervalo_bootstrap([]) is None


def test_bootstrap_con_otro_estadistico():  # para remuestrear audios y juntar sus recuentos
    pares = [(1, 2), (1, 2), (1, 2)]
    assert metricas.intervalo_bootstrap(pares, estadistico=lambda m: sum(a for a, _ in m)) == (
        3,
        3,
    )


# --- M-01: DER con pyannote.metrics, estricto (sin margen y con solapamientos) -------------


@pytest.fixture
def pyannote_metrics():
    return pytest.importorskip("pyannote.metrics")


def test_der_sin_errores_aunque_los_nombres_cambien(pyannote_metrics):
    d = metricas.der(
        [("FEE005", 0.0, 10.0), ("MEE006", 10.0, 20.0)], [("1", 0.0, 10.0), ("2", 10.0, 20.0)]
    )
    assert (d.error, d.total, d.valor) == (0.0, 20.0, 0.0)


def test_der_confunde_dos_voces_en_una(pyannote_metrics):
    d = metricas.der([("a", 0.0, 10.0), ("b", 10.0, 20.0)], [("x", 0.0, 20.0)])
    assert d.valor == pytest.approx(0.5)


def test_der_cuenta_el_solapamiento(pyannote_metrics):  # sin skip_overlap
    d = metricas.der([("a", 0.0, 10.0), ("b", 5.0, 10.0)], [("x", 0.0, 10.0)])
    assert d.total == 15.0
    assert d.valor == pytest.approx(5 / 15)


def test_der_sin_margen_en_los_bordes(pyannote_metrics):  # collar 0
    d = metricas.der([("a", 0.0, 10.0)], [("x", 0.0, 9.9)])
    assert d.error == pytest.approx(0.1)


def test_der_de_varias_reuniones_suma_errores_y_tiempos():
    juntos = metricas.der_conjunto([metricas.Der(1.0, 10.0), metricas.Der(3.0, 30.0)])
    assert juntos == metricas.Der(4.0, 40.0)
    assert juntos.valor == 0.1
    assert metricas.Der(0.0, 0.0).valor is None


def test_bootstrap_ignora_las_muestras_en_las_que_no_se_aplica():  # RN-13: un None no es un 0
    def solo_con_eventos(muestra):
        return None if all(x == 0 for x in muestra) else 1.0

    assert metricas.intervalo_bootstrap([0, 1], estadistico=solo_con_eventos) == (1.0, 1.0)
    assert metricas.intervalo_bootstrap([0], estadistico=solo_con_eventos) is None


# --- M-02 y M-03: acierto de la propuesta de voz, por hablante --------------------------------

F, M, IND = c.EtiquetaVoz.FEMENINO, c.EtiquetaVoz.MASCULINO, c.EtiquetaVoz.INDETERMINADO


def test_error_de_un_grupo():  # M-03
    pares = [(F, F), (F, M), (M, M), (M, M)]  # (referencia, propuesta)
    assert metricas.error_de_grupo(pares, F) == 0.5
    assert metricas.error_de_grupo(pares, M) == 0.0


def test_indeterminado_cuenta_como_fallo():  # decisión del 25 oct 2026
    assert metricas.error_de_grupo([(F, IND), (F, F)], F) == 0.5


def test_error_de_un_grupo_sin_voces_no_se_aplica():  # RN-13
    assert metricas.error_de_grupo([(M, M)], F) is None


def test_exactitud_equilibrada_es_la_media_del_acierto_de_cada_grupo():  # M-02
    pares = [(F, F), (F, F), (F, M), (M, M)]  # acierta 2 de 3 F y 1 de 1 M
    assert metricas.exactitud_equilibrada(pares) == pytest.approx((2 / 3 + 1) / 2)


def test_exactitud_con_un_solo_grupo_es_su_acierto():
    assert metricas.exactitud_equilibrada([(F, F), (F, IND)]) == 0.5


def test_exactitud_sin_voces_no_se_aplica():
    assert metricas.exactitud_equilibrada([]) is None


def test_diferencia_entre_grupos_en_puntos():  # M-03, RNF-06
    pares = [(F, F), (F, IND), (M, M), (M, M), (M, M), (M, F)]  # 50 % frente a 25 %
    assert metricas.diferencia_entre_grupos(pares) == pytest.approx(25.0)


def test_diferencia_sin_uno_de_los_grupos_no_se_aplica():  # RN-13
    assert metricas.diferencia_entre_grupos([(F, F), (F, M)]) is None


# --- Intervalos de la voz: Wilson y MOVER-Wilson (por qué no bootstrap: con todo acertado, da 1 a 1)


def test_wilson_con_todo_acertado_no_da_un_intervalo_vacio():
    bajo, alto = metricas.intervalo_wilson(17, 17)
    assert bajo == pytest.approx(0.8157, abs=1e-4)
    assert alto == pytest.approx(1.0)


def test_wilson_sin_ningun_fallo():
    assert metricas.intervalo_wilson(0, 9) == pytest.approx((0.0, 0.2991), abs=1e-4)


def test_wilson_sin_casos_no_se_aplica():
    assert metricas.intervalo_wilson(0, 0) is None


PERFECTO = [(F, F)] * 9 + [(M, M)] * 8  # lo medido en OVH el 26 oct 2026


def test_intervalo_del_error_de_un_grupo():  # M-03
    assert metricas.intervalo_error_de_grupo(PERFECTO, F) == pytest.approx((0.0, 0.2991), abs=1e-4)
    assert metricas.intervalo_error_de_grupo(PERFECTO, M) == pytest.approx((0.0, 0.3244), abs=1e-4)
    assert metricas.intervalo_error_de_grupo([(M, M)], F) is None


def test_intervalo_de_la_exactitud_equilibrada_junta_los_dos_grupos():  # M-02, MOVER-Wilson
    bajo, alto = metricas.intervalo_exactitud_equilibrada(PERFECTO)
    assert bajo == pytest.approx(0.7794, abs=1e-4)
    assert alto == pytest.approx(1.0)


def test_intervalo_de_la_exactitud_con_un_solo_grupo_es_su_wilson():
    assert metricas.intervalo_exactitud_equilibrada([(F, F)] * 9) == pytest.approx(
        metricas.intervalo_wilson(9, 9)
    )


def test_intervalo_de_la_diferencia_entre_grupos_en_puntos():  # M-03, Newcombe
    bajo, alto = metricas.intervalo_diferencia_entre_grupos(PERFECTO)
    assert bajo == 0.0  # la diferencia es un valor absoluto
    assert alto == pytest.approx(32.44, abs=0.01)
    assert metricas.intervalo_diferencia_entre_grupos([(F, F)]) is None


def test_voces_de_cada_grupo():
    assert metricas.voces_de_grupo(PERFECTO, F) == 9
    assert metricas.voces_de_grupo(PERFECTO, M) == 8
