"""Pruebas del contrato de datos (RD-02). Cada caso cita la regla del funcional que comprueba."""

import re

import pytest
from pydantic import BaseModel, ValidationError

import contrato as c


def turno(hablante, inicio, fin):
    return {"hablante": hablante, "inicio": inicio, "fin": fin}


# --- Valores cerrados -----------------------------------------------------------------------


def test_etiquetas_de_voz_son_tres():  # RN-03
    assert {e.value for e in c.EtiquetaVoz} == {"femenino", "masculino", "indeterminado"}


def test_origen_de_la_etiqueta():  # RF-07
    assert {o.value for o in c.OrigenEtiqueta} == {"modelo", "persona"}


def test_estados_del_analisis():  # RF-04
    assert {e.value for e in c.Estado} == {
        "en_cola",
        "procesando",
        "esperando_confirmacion",
        "terminado",
        "error",
    }


def test_tipos_de_solapamiento():  # 6.7, RN-07
    assert {t.value for t in c.TipoSolapamiento} == {"con_exito", "intento", "senal_de_escucha"}


def test_solo_con_exito_e_intento_cuentan_como_interrupcion():  # RN-07
    assert c.TipoSolapamiento.CON_EXITO.cuenta_como_interrupcion
    assert c.TipoSolapamiento.INTENTO.cuenta_como_interrupcion
    assert not c.TipoSolapamiento.SENAL_DE_ESCUCHA.cuenta_como_interrupcion


def test_indices_de_grupo():  # RF-16: los dos Must
    assert {i.value for i in c.NombreIndice} == {"ratio_representacion", "brecha_interrupcion"}


# --- Formato de intercambio (9.4) -----------------------------------------------------------


def _modelos():
    return [
        obj
        for obj in vars(c).values()
        if isinstance(obj, type) and issubclass(obj, BaseModel) and obj.__module__ == c.__name__
    ]


def test_nombres_de_campo_en_espanol_sin_tildes():  # 9.4
    for modelo in _modelos():
        for campo in modelo.model_fields:
            assert re.fullmatch(r"[a-z][a-z0-9_]*", campo), f"{modelo.__name__}.{campo}"


def test_mensajes_llevan_version_contrato_por_defecto():  # 9.4
    estado = c.EstadoAnalisis(id_analisis="a1", estado="en_cola")
    assert estado.version_contrato == c.VERSION_CONTRATO


def test_rechaza_otra_version_contrato():  # 9.4
    with pytest.raises(ValidationError):
        c.EstadoAnalisis(version_contrato="9.9", id_analisis="a1", estado="en_cola")


def test_rechaza_campos_desconocidos():
    with pytest.raises(ValidationError):
        c.Turno(hablante=1, inicio=0.0, fin=1.0, orador=1)


def test_ida_y_vuelta_por_json():  # 9.4
    estado = c.EstadoAnalisis(id_analisis="a1", estado="procesando", progreso=40.5)
    assert c.EstadoAnalisis.model_validate_json(estado.model_dump_json()) == estado


# --- Tiempos y hablantes --------------------------------------------------------------------


def test_turno_valido():  # RF-05, 9.4: segundos con decimales
    t = c.Turno(**turno(1, 0.25, 3.5))
    assert (t.hablante, t.inicio, t.fin) == (1, 0.25, 3.5)


@pytest.mark.parametrize(("inicio", "fin"), [(2.0, 2.0), (3.0, 1.0), (-0.1, 1.0)])
def test_turno_rechaza_tiempos_imposibles(inicio, fin):
    with pytest.raises(ValidationError):
        c.Turno(**turno(1, inicio, fin))


def test_hablante_se_numera_desde_1():  # RN-10: «Hablante n»
    with pytest.raises(ValidationError):
        c.Turno(**turno(0, 0.0, 1.0))


def test_solapamiento_necesita_dos_hablantes_distintos():  # RF-05
    c.Solapamiento(hablantes=[1, 2], inicio=1.0, fin=1.5)
    with pytest.raises(ValidationError):
        c.Solapamiento(hablantes=[1], inicio=1.0, fin=1.5)
    with pytest.raises(ValidationError):
        c.Solapamiento(hablantes=[1, 1], inicio=1.0, fin=1.5)


# --- Propuesta y confirmación de voz --------------------------------------------------------


@pytest.mark.parametrize("confianza", [0.0, 0.5, 1.0])
def test_confianza_entre_0_y_1(confianza):  # RF-06
    c.PropuestaVoz(etiqueta="femenino", confianza=confianza)


@pytest.mark.parametrize("confianza", [-0.01, 1.01])
def test_confianza_fuera_de_rango(confianza):  # RF-06
    with pytest.raises(ValidationError):
        c.PropuestaVoz(etiqueta="femenino", confianza=confianza)


def test_hablante_sin_propuesta_en_modo_manual():  # RF-08
    h = c.Hablante(hablante=1, segundos_habla=12.0, fragmentos=[{"inicio": 0.0, "fin": 3.0}])
    assert h.propuesta is None


def test_hablantes_para_confirmar_sin_repetidos():  # RF-07
    h = {"hablante": 1, "segundos_habla": 12.0, "fragmentos": []}
    with pytest.raises(ValidationError):
        c.HablantesParaConfirmar(id_analisis="a1", hablantes=[h, h])


def test_confirmacion_valida():  # RF-07
    conf = c.Confirmacion(
        etiquetas=[
            {"hablante": 1, "etiqueta": "femenino", "origen": "modelo"},
            {"hablante": 2, "etiqueta": "indeterminado", "origen": "persona"},
        ]
    )
    assert len(conf.etiquetas) == 2


def test_confirmacion_rechaza_hablante_repetido():  # RF-07
    e = {"hablante": 1, "etiqueta": "femenino", "origen": "persona"}
    with pytest.raises(ValidationError):
        c.Confirmacion(etiquetas=[e, e])


def test_confirmacion_no_puede_estar_vacia():  # RF-07
    with pytest.raises(ValidationError):
        c.Confirmacion(etiquetas=[])


# --- Estado del análisis (RF-04, RNF-16) ----------------------------------------------------


def test_error_exige_motivo():  # RF-04, RNF-16
    with pytest.raises(ValidationError):
        c.EstadoAnalisis(id_analisis="a1", estado="error")
    c.EstadoAnalisis(id_analisis="a1", estado="error", motivo_error="El audio no es válido")


def test_motivo_solo_en_error():  # RF-04
    with pytest.raises(ValidationError):
        c.EstadoAnalisis(id_analisis="a1", estado="terminado", motivo_error="x")


def test_procesando_exige_progreso():  # RF-04: «procesando con % de avance»
    with pytest.raises(ValidationError):
        c.EstadoAnalisis(id_analisis="a1", estado="procesando")


def test_progreso_solo_en_procesando():  # RF-04
    with pytest.raises(ValidationError):
        c.EstadoAnalisis(id_analisis="a1", estado="en_cola", progreso=10.0)


@pytest.mark.parametrize("progreso", [-1.0, 100.5])
def test_progreso_entre_0_y_100(progreso):  # RF-04
    with pytest.raises(ValidationError):
        c.EstadoAnalisis(id_analisis="a1", estado="procesando", progreso=progreso)


# --- Entrada del análisis -------------------------------------------------------------------


def entrada(**cambios):
    datos = {
        "duracion": 20.0,
        "turnos": [turno(1, 0.0, 10.0), turno(2, 9.5, 20.0)],
        "solapamientos": [{"hablantes": [1, 2], "inicio": 9.5, "fin": 10.0}],
        "etiquetas": [
            {"hablante": 1, "etiqueta": "femenino", "origen": "modelo"},
            {"hablante": 2, "etiqueta": "masculino", "origen": "persona"},
        ],
    }
    datos.update(cambios)
    return datos


def test_entrada_valida():
    assert len(c.EntradaAnalisis(**entrada()).turnos) == 2


def test_entrada_rechaza_tramo_mas_alla_de_la_duracion():
    with pytest.raises(ValidationError):
        c.EntradaAnalisis(**entrada(duracion=15.0))


def test_entrada_rechaza_etiqueta_de_hablante_sin_turnos():
    etiquetas = [{"hablante": 3, "etiqueta": "femenino", "origen": "persona"}]
    with pytest.raises(ValidationError):
        c.EntradaAnalisis(**entrada(etiquetas=etiquetas))


def test_entrada_rechaza_solapamiento_de_hablante_sin_turnos():
    solapamientos = [{"hablantes": [1, 3], "inicio": 9.5, "fin": 10.0}]
    with pytest.raises(ValidationError):
        c.EntradaAnalisis(**entrada(solapamientos=solapamientos))


# --- Resultado ------------------------------------------------------------------------------


def test_indice_no_aplicable_es_none_nunca_cero():  # RN-13
    i = c.Indice(nombre="brecha_interrupcion", valor=None, formula="BI = ...")
    assert i.valor is None
    assert not i.aplicable


def test_indice_aplicable():  # RF-16
    assert c.Indice(nombre="ratio_representacion", valor=0.8, formula="RR = ...").aplicable


def test_indice_exige_formula():  # RN-06
    with pytest.raises(ValidationError):
        c.Indice(nombre="ratio_representacion", valor=0.8, formula="")


def test_interrupcion_entre_hablantes_distintos():  # RF-14
    c.Interrupcion(interrumpe=2, interrumpido=1, tipo="intento", inicio=4.0, fin=6.0)
    with pytest.raises(ValidationError):
        c.Interrupcion(interrumpe=1, interrumpido=1, tipo="intento", inicio=4.0, fin=6.0)


@pytest.mark.parametrize("campo", ["cuota_tiempo", "cuota_turnos"])
def test_cuotas_en_porcentaje(campo):  # MD-04, MD-05
    grupo = {
        "etiqueta": "femenino",
        "numero_voces": 1,
        "segundos_habla": 10.0,
        "turnos": 2,
        "interrupciones_recibidas": 0,
    }
    with pytest.raises(ValidationError):
        c.MetricasGrupo(**grupo, **{campo: 100.5})


def test_resultado_rechaza_grupo_repetido():
    grupo = {
        "etiqueta": "femenino",
        "numero_voces": 1,
        "segundos_habla": 10.0,
        "turnos": 2,
        "interrupciones_recibidas": 0,
    }
    with pytest.raises(ValidationError):
        c.Resultado(
            id_analisis="a1",
            duracion=20.0,
            voz_femenina_presente=True,
            grupos=[grupo, grupo],
            hablantes=[],
            turnos=[],
            solapamientos=[],
            interrupciones=[],
            indices=[],
        )
