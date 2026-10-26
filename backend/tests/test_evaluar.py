"""Pruebas de evaluar.py (B12): junta referencias y salidas guardadas y calcula la tabla de 12.1."""

import pytest
from ayudas import cargar_ejemplo, entrada_de

import contrato as c
from analisis.analizar import analizar
from evaluacion import cronometrar, evaluar, lectura, metricas

# Referencia de una reunión: FIO093 habla 4 s y es una voz corta (RN-01, D-15)
TRAMOS = [("FIE038", 0.0, 20.0), ("MIO091", 19.5, 35.0), ("FIO093", 41.0, 45.0)]


def escribir_rttm(ruta, tramos):
    ruta.write_text(
        "".join(
            f"SPEAKER x 1 {i:.2f} {f - i:.2f} <NA> <NA> {codigo} <NA> <NA>\n"
            for codigo, i, f in tramos
        ),
        encoding="utf-8",
    )


def escribir_resultado(ruta, resultado):
    ruta.write_text(resultado.model_dump_json(), encoding="utf-8")


def resultado_de(tramos, **cambios):
    entrada, _ = lectura.entrada_de_referencia(tramos)
    if cambios:
        entrada = entrada.model_copy(update=cambios)
    return analizar(entrada)


@pytest.fixture
def carpetas(tmp_path):
    ami, salidas, etiquetas = tmp_path / "ami", tmp_path / "salidas", tmp_path / "etiquetas"
    for carpeta in (ami, salidas, etiquetas):
        carpeta.mkdir()
    return ami, salidas, etiquetas


def test_las_reuniones_de_prueba_son_las_del_funcional():  # 11.3
    assert evaluar.REUNIONES_PRUEBA == ("EN2002a", "EN2002c", "ES2004a", "IS1009a", "TS3003a")


# --- Lo que se saca de un Resultado guardado --------------------------------------------------


@pytest.mark.parametrize("nombre", ["con_voces_femeninas", "muchas_interrupciones"])
def test_entrada_del_resultado(nombre):
    resultado = cargar_ejemplo(nombre)
    assert evaluar.entrada_del_resultado(resultado) == entrada_de(resultado)


def test_inicios_solo_de_lo_que_cuenta_como_interrupcion():  # RN-07
    resultado = cargar_ejemplo("muchas_interrupciones")
    esperados = sorted(
        i.inicio for i in resultado.interrupciones if i.tipo.cuenta_como_interrupcion
    )
    assert evaluar.inicios(resultado) == esperados
    assert len(esperados) < len(resultado.interrupciones)  # hay señales de escucha que no cuentan


def test_cuota_femenina():
    resultado = cargar_ejemplo("con_voces_femeninas")
    (fem,) = [g for g in resultado.grupos if g.etiqueta is c.EtiquetaVoz.FEMENINO]
    assert evaluar.cuota_femenina(resultado) == fem.cuota_tiempo


# --- AMI: M-01, M-04 y la ablación --------------------------------------------------------


def test_reunion_igual_que_la_referencia(carpetas):
    pytest.importorskip("pyannote.metrics")
    ami, salidas, _ = carpetas
    escribir_rttm(ami / "EN2002a.rttm", TRAMOS)
    escribir_rttm(salidas / "EN2002a.rttm", [(str(n), i, f) for n, (_, i, f) in enumerate(TRAMOS)])
    escribir_resultado(salidas / "EN2002a.json", resultado_de(TRAMOS))

    (reunion,) = evaluar.evaluar_ami(ami, salidas)
    assert reunion.nombre == "EN2002a"
    assert reunion.der.valor == 0.0
    assert reunion.error_femenino == 0.0  # M-04
    assert reunion.ablacion.falsos == reunion.ablacion.perdidos == 0
    assert not reunion.ideal  # con el .json se usa el resultado del sistema


def test_m04_compara_con_la_referencia_de_ami(carpetas):
    pytest.importorskip("pyannote.metrics")
    ami, salidas, _ = carpetas
    escribir_rttm(ami / "EN2002a.rttm", TRAMOS)
    escribir_rttm(salidas / "EN2002a.rttm", TRAMOS)
    # el sistema confirma como femenina la voz masculina
    referencia = resultado_de(TRAMOS)
    sistema = resultado_de(
        TRAMOS,
        etiquetas=[
            c.EtiquetaConfirmada(hablante=h, etiqueta="femenino", origen="persona") for h in (1, 3)
        ],
    )
    escribir_resultado(salidas / "EN2002a.json", sistema)

    (reunion,) = evaluar.evaluar_ami(ami, salidas)
    esperado = abs(evaluar.cuota_femenina(sistema) - evaluar.cuota_femenina(referencia))
    assert reunion.error_femenino == pytest.approx(esperado, abs=0.01)
    assert reunion.error_femenino > 0


def test_reunion_sin_salidas_se_salta(carpetas):  # n cuenta solo lo evaluado
    ami, salidas, _ = carpetas
    escribir_rttm(ami / "EN2002a.rttm", TRAMOS)
    assert evaluar.evaluar_ami(ami, salidas) == []


def test_solo_se_evaluan_las_reuniones_de_prueba(carpetas):  # RD-05, constitución 9
    pytest.importorskip("pyannote.metrics")
    ami, salidas, _ = carpetas
    for nombre in ("IB4002", "EN2002a"):  # IB4002 es de desarrollo
        escribir_rttm(ami / f"{nombre}.rttm", TRAMOS)
        escribir_rttm(salidas / f"{nombre}.rttm", TRAMOS)
        escribir_resultado(salidas / f"{nombre}.json", resultado_de(TRAMOS))
    assert [r.nombre for r in evaluar.evaluar_ami(ami, salidas)] == ["EN2002a"]


# --- Grabaciones anotadas: M-05, línea base y M-08 -----------------------------------------


def escribir_etiquetas(ruta, anotaciones):
    ruta.write_text(
        "".join(f"{a.inicio}\t{a.fin}\t{a.tipo}\n" for a in anotaciones), encoding="utf-8"
    )


def test_grabacion_anotada(carpetas):
    _, salidas, etiquetas = carpetas
    resultado = cargar_ejemplo("muchas_interrupciones")
    escribir_resultado(salidas / "grabacion1.json", resultado)
    referencia = [
        lectura.Anotacion(i.inicio, i.fin, "intento")
        for i in resultado.interrupciones
        if i.tipo.cuenta_como_interrupcion
    ]
    escribir_etiquetas(etiquetas / "grabacion1_referencia.txt", referencia)
    a = [lectura.Anotacion(1.0, 2.0, "intento"), lectura.Anotacion(9.0, 10.0, "con_exito")]
    escribir_etiquetas(etiquetas / "grabacion1_A.txt", a)
    escribir_etiquetas(etiquetas / "grabacion1_C.txt", a)

    (grabacion,) = evaluar.evaluar_grabaciones(etiquetas, salidas)
    assert grabacion.nombre == "grabacion1"
    assert grabacion.sistema.f1 == 1.0  # M-05
    base = metricas.linea_base(evaluar.entrada_del_resultado(resultado))
    assert grabacion.linea_base == metricas.deteccion(base, [x.inicio for x in referencia])
    assert grabacion.kappa == 1.0  # M-08


def test_en2002a_solo_esta_anotada_hasta_el_minuto_5():  # guía de anotación, apartado 2
    assert evaluar.ANOTADO_HASTA == {"EN2002a": 300.0}


def test_solo_se_compara_la_parte_anotada_del_audio(carpetas, monkeypatch):
    """Lo que el sistema detecta después de donde acaba la anotación no cuenta como fallo."""
    _, salidas, etiquetas = carpetas
    resultado = cargar_ejemplo("muchas_interrupciones")
    escribir_resultado(salidas / "grabacion1.json", resultado)
    todas = evaluar.inicios(resultado)
    assert len(todas) >= 2
    hasta = (todas[0] + todas[1]) / 2  # solo la primera interrupción queda en la parte anotada
    monkeypatch.setattr(evaluar, "ANOTADO_HASTA", {"grabacion1": hasta})
    escribir_etiquetas(
        etiquetas / "grabacion1_referencia.txt",
        [lectura.Anotacion(todas[0], todas[0] + 1.0, "intento")],
    )

    (grabacion,) = evaluar.evaluar_grabaciones(etiquetas, salidas)
    assert grabacion.sistema == metricas.Deteccion(verdaderos=1, falsos=0, perdidos=0)
    base = metricas.linea_base(evaluar.entrada_del_resultado(resultado))
    esperada = metricas.deteccion([x for x in base if x < hasta], [todas[0]])
    assert grabacion.linea_base == esperada


def test_sin_la_otra_anotadora_la_kappa_no_se_aplica(carpetas):
    _, salidas, etiquetas = carpetas
    escribir_resultado(salidas / "g.json", cargar_ejemplo("con_voces_femeninas"))
    escribir_etiquetas(etiquetas / "g_referencia.txt", [])
    escribir_etiquetas(etiquetas / "g_A.txt", [lectura.Anotacion(1.0, 2.0, "intento")])
    (grabacion,) = evaluar.evaluar_grabaciones(etiquetas, salidas)
    assert grabacion.kappa is None


def test_sin_referencia_o_sin_salida_no_se_evalua(carpetas):
    _, salidas, etiquetas = carpetas
    escribir_etiquetas(etiquetas / "sola_A.txt", [])  # aún sin referencia de consenso
    escribir_etiquetas(etiquetas / "sin_salida_referencia.txt", [])
    assert evaluar.evaluar_grabaciones(etiquetas, salidas) == []


# --- Informe y línea de comandos ---------------------------------------------------------


def test_informe_sin_datos_dice_no_aplicable():  # RN-13
    texto = evaluar.informe([], [])
    for metrica in ("M-01", "M-04", "M-05", "M-08"):
        assert metrica in texto
    assert "no aplicable" in texto
    assert "n = 0" in texto


def test_informe_con_una_reunion_y_una_grabacion():
    reunion = evaluar.Reunion("EN2002a", metricas.Der(2.0, 10.0), 1.5, metricas.Deteccion(2, 0, 0))
    grabacion = evaluar.Grabacion(
        "g", metricas.Deteccion(3, 1, 0), metricas.Deteccion(3, 5, 0), 0.8
    )
    texto = evaluar.informe([reunion], [grabacion])
    assert "20,0 %" in texto  # DER
    assert "1,50 puntos" in texto  # M-04
    assert "0,86" in texto  # F1 = 6 / 7
    assert "0,80" in texto  # kappa
    assert "n = 1" in texto


def test_main_escribe_el_informe(carpetas, capsys):
    ami, salidas, etiquetas = carpetas
    codigo = evaluar.main(
        ["--ami", str(ami), "--salidas", str(salidas), "--etiquetas", str(etiquetas)]
    )
    assert codigo == 0
    assert "M-01" in capsys.readouterr().out


def test_main_avisa_si_falta_una_carpeta(tmp_path, capsys):
    codigo = evaluar.main(["--salidas", str(tmp_path / "no_existe")])
    assert codigo == 2
    assert "no_existe" in capsys.readouterr().err


def test_solo_con_el_rttm_se_calcula_el_der(carpetas):  # el comando de A guarda solo el .rttm
    pytest.importorskip("pyannote.metrics")
    ami, salidas, _ = carpetas
    escribir_rttm(ami / "EN2002a.rttm", TRAMOS)
    escribir_rttm(salidas / "EN2002a.rttm", TRAMOS)

    (reunion,) = evaluar.evaluar_ami(ami, salidas)
    assert reunion.der.valor == 0.0
    # sin el .json, M-04 y la ablación salen con la confirmación ideal
    assert reunion.ideal
    assert reunion.error_femenino == 0.0
    assert reunion.ablacion.falsos == reunion.ablacion.perdidos == 0


def test_sin_json_m04_y_la_ablacion_no_cuentan_en_n():  # RN-13: lo que falta no se inventa
    reunion = evaluar.Reunion("EN2002a", metricas.Der(2.0, 10.0), None, None)
    texto = evaluar.informe([reunion], [])
    filas = {linea.split(" | ")[0]: linea for linea in texto.splitlines() if linea.startswith("| ")}
    assert filas["| M-01, DER (reuniones de AMI)"].endswith("n = 1 |")
    assert filas["| M-04, error del % femenino"].endswith("n = 0 |")
    ablacion = next(v for k, v in filas.items() if k.startswith("| Ablación"))
    assert ablacion.endswith("n = 0 |")


# --- Confirmación ideal: solo para medir en AMI, donde nadie confirma a mano ---------------


def etiquetas_de(resultado):
    return {h.hablante: h.etiqueta for h in resultado.hablantes}


def test_cada_voz_recibe_el_sexo_de_quien_mas_coincide():  # funcional, 11.2
    sistema = [("hablante_1", 0.0, 20.2), ("hablante_2", 20.2, 35.0), ("hablante_3", 41.0, 45.0)]
    resultado = evaluar.resultado_ideal(sistema, TRAMOS)
    # el 3 habla 4 s: voz corta, sin etiqueta (RN-01)
    assert etiquetas_de(resultado) == {1: c.EtiquetaVoz.FEMENINO, 2: c.EtiquetaVoz.MASCULINO}


def test_las_voces_se_numeran_por_orden_de_aparicion():  # como diarizacion.py
    sistema = [("B", 20.0, 35.0), ("A", 0.0, 20.0)]
    resultado = evaluar.resultado_ideal(sistema, TRAMOS)
    assert etiquetas_de(resultado) == {1: c.EtiquetaVoz.FEMENINO, 2: c.EtiquetaVoz.MASCULINO}


def test_una_voz_que_junta_a_dos_personas_se_queda_con_la_mayoria():
    sistema = [("x", 0.0, 35.0)]  # 20 s de FIE038 y 15,5 s de MIO091
    resultado = evaluar.resultado_ideal(sistema, TRAMOS)
    assert etiquetas_de(resultado) == {1: c.EtiquetaVoz.FEMENINO}


def test_una_voz_donde_ami_no_tiene_a_nadie_queda_sin_etiqueta():
    sistema = [("x", 0.0, 20.0), ("y", 50.0, 70.0)]  # en AMI nadie habla después de 45 s
    resultado = evaluar.resultado_ideal(sistema, TRAMOS)
    assert etiquetas_de(resultado) == {1: c.EtiquetaVoz.FEMENINO}
    assert resultado.segundos_voces_cortas == 20.0  # su tiempo se ve aparte (D-15)


def test_el_informe_avisa_de_la_confirmacion_ideal():
    reunion = evaluar.Reunion(
        "EN2002a", metricas.Der(2.0, 10.0), 1.5, metricas.Deteccion(2, 0, 0), ideal=True
    )
    assert "confirmación ideal" in evaluar.informe([reunion], [])
    assert "confirmación ideal" not in evaluar.informe([], [])


# --- M-02 y M-03: propuesta de voz frente al sexo registrado en AMI ----------------------------

F, M, IND = c.EtiquetaVoz.FEMENINO, c.EtiquetaVoz.MASCULINO, c.EtiquetaVoz.INDETERMINADO
MODELO, PERSONA = c.OrigenEtiqueta.MODELO, c.OrigenEtiqueta.PERSONA


def con_etiquetas(*etiquetas):
    """TRAMOS se numeran por orden alfabético: 1 = FIE038 (F), 3 = MIO091 (M); 2 es voz corta."""
    return resultado_de(
        TRAMOS,
        etiquetas=[c.EtiquetaConfirmada(hablante=h, etiqueta=e, origen=o) for h, e, o in etiquetas],
    )


def test_cada_voz_propuesta_se_compara_con_el_sexo_de_quien_mas_coincide():  # M-02, 11.2
    resultado = con_etiquetas((1, F, MODELO), (3, IND, MODELO))
    assert evaluar.voces_propuestas(resultado, TRAMOS) == [(F, F), (M, IND)]


def test_las_voces_confirmadas_por_una_persona_no_miden_el_modelo():
    resultado = con_etiquetas((1, F, PERSONA), (3, M, MODELO))
    assert evaluar.voces_propuestas(resultado, TRAMOS) == [(M, M)]


def test_la_reunion_guarda_las_voces_propuestas(carpetas):
    pytest.importorskip("pyannote.metrics")
    ami, salidas, _ = carpetas
    escribir_rttm(ami / "EN2002a.rttm", TRAMOS)
    escribir_rttm(salidas / "EN2002a.rttm", TRAMOS)
    escribir_resultado(salidas / "EN2002a.json", con_etiquetas((1, F, MODELO), (3, F, MODELO)))

    (reunion,) = evaluar.evaluar_ami(ami, salidas)
    assert reunion.voces == ((F, F), (M, F))


def test_con_la_confirmacion_ideal_no_hay_voces_propuestas(carpetas):
    pytest.importorskip("pyannote.metrics")
    ami, salidas, _ = carpetas
    escribir_rttm(ami / "EN2002a.rttm", TRAMOS)
    escribir_rttm(salidas / "EN2002a.rttm", TRAMOS)
    (reunion,) = evaluar.evaluar_ami(ami, salidas)
    assert reunion.voces == ()


def filas_del(texto):
    return {linea.split(" | ")[0]: linea for linea in texto.splitlines() if linea.startswith("| ")}


def test_el_informe_publica_m02_y_m03_por_hablante():  # RNF-03 y RNF-06: Must publicarlas
    voces = ((F, F), (F, IND), (M, M), (M, M))
    reunion = evaluar.Reunion("EN2002a", metricas.Der(0.0, 10.0), None, None, voces=voces)
    filas = filas_del(evaluar.informe([reunion], []))
    assert filas["| M-02, exactitud equilibrada de la voz"].startswith(
        "| M-02, exactitud equilibrada de la voz | 0,75 |"
    )
    assert filas["| M-02, exactitud equilibrada de la voz"].endswith("n = 4 |")
    assert "| 50,0 % |" in filas["| M-03, error de la voz femenina"]
    assert "| 0,0 % |" in filas["| M-03, error de la voz masculina"]
    assert "| 50,0 puntos |" in filas["| M-03, diferencia entre grupos"]
    assert filas["| M-03, error de la voz femenina"].endswith("n = 2 |")  # n de su grupo
    assert filas["| M-03, error de la voz masculina"].endswith("n = 2 |")


def test_con_todas_las_voces_acertadas_el_intervalo_no_es_1_a_1():  # lo medido el 26 oct 2026
    voces = ((F, F),) * 9 + ((M, M),) * 8
    reunion = evaluar.Reunion("EN2002a", metricas.Der(0.0, 10.0), None, None, voces=voces)
    filas = filas_del(evaluar.informe([reunion], []))
    assert filas["| M-02, exactitud equilibrada de la voz"] == (
        "| M-02, exactitud equilibrada de la voz | 1,00 | 0,78 a 1,00 | n = 17 |"
    )
    assert filas["| M-03, error de la voz femenina"] == (
        "| M-03, error de la voz femenina | 0,0 % | 0,0 % a 29,9 % | n = 9 |"
    )
    assert filas["| M-03, error de la voz masculina"] == (
        "| M-03, error de la voz masculina | 0,0 % | 0,0 % a 32,4 % | n = 8 |"
    )
    assert filas["| M-03, diferencia entre grupos"] == (
        "| M-03, diferencia entre grupos | 0,0 puntos | 0,0 puntos a 32,4 puntos | n = 9 + 8 |"
    )


def test_el_informe_publica_m09_con_la_mediana():  # RNF-01: mediana de 3 audios
    filas = filas_del(evaluar.informe([], [], tiempos=[2.0, 3.0, 10.0]))
    fila = filas["| M-09, minutos de proceso por hora de audio (mediana)"]
    assert "| 3,0 min |" in fila
    assert fila.endswith("n = 3 |")


def test_main_lee_los_tiempos_guardados(carpetas, capsys):  # M-09
    ami, salidas, etiquetas = carpetas
    cronometrar.guardar(salidas / "EN2002a.tiempo.json", duracion_audio=3600.0, segundos=360.0)
    evaluar.main(["--salidas", str(salidas), "--ami", str(ami), "--etiquetas", str(etiquetas)])
    assert "| 6,0 min |" in capsys.readouterr().out
