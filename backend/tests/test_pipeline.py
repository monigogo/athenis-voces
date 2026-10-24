"""Pruebas del pipeline: orden de los pasos, estados (RF-04) y errores (RNF-16), con pasos falsos."""

from pathlib import Path

import pytest

import contrato as c
import pipeline as p

ID = "a1"
DURACION = 45.0
# El hablante 3 habla 4 s: no es una voz presente (RN-01) y no pasa a confirmación.
TURNOS = [
    c.Turno(hablante=1, inicio=0.0, fin=20.0),
    c.Turno(hablante=2, inicio=19.5, fin=40.0),
    c.Turno(hablante=3, inicio=41.0, fin=45.0),
]
SOLAPAMIENTOS = [c.Solapamiento(hablantes=[1, 2], inicio=19.5, fin=20.0)]
PROPUESTAS = {
    1: c.PropuestaVoz(etiqueta="femenino", confianza=0.9),
    2: c.PropuestaVoz(etiqueta="masculino", confianza=0.8),
    3: c.PropuestaVoz(etiqueta="indeterminado", confianza=0.5),
}
FRAGMENTOS = {
    1: [c.Fragmento(inicio=0.0, fin=3.0), c.Fragmento(inicio=5.0, fin=9.0)],
    2: [c.Fragmento(inicio=25.0, fin=29.0)],
}
EJEMPLO = Path(__file__).parent / "ejemplos" / "con_voces_femeninas.json"


class Falsos:
    """Pasos falsos que apuntan lo que se llama y con qué."""

    def __init__(self, falla=None, propuestas=PROPUESTAS):
        self.llamadas = []
        self.falla = falla
        self.propuestas = propuestas
        self.destino = None
        self.entrada = None

    def _anotar(self, nombre):
        self.llamadas.append(nombre)
        if nombre == self.falla:
            raise RuntimeError("roto")

    def preparar(self, origen, destino):
        self._anotar("preparar")
        self.destino = destino
        return DURACION

    def diarizar(self, wav):
        self._anotar("diarizar")
        return TURNOS, SOLAPAMIENTOS

    def proponer_voz(self, wav, turnos):
        self._anotar("proponer_voz")
        return self.propuestas

    def elegir_fragmentos(self, turnos, solapamientos):
        self._anotar("elegir_fragmentos")
        return FRAGMENTOS

    def analizar(self, entrada):
        self._anotar("analizar")
        self.entrada = entrada
        return c.Resultado.model_validate_json(EJEMPLO.read_text(encoding="utf-8"))

    def pasos(self):
        return p.Pasos(
            preparar=self.preparar,
            diarizar=self.diarizar,
            proponer_voz=self.proponer_voz,
            elegir_fragmentos=self.elegir_fragmentos,
            analizar=self.analizar,
        )


def fase_1(tmp_path, falsos, estados, **opciones):
    return p.preparar_para_confirmar(
        ID, tmp_path / "subido.mp3", tmp_path, falsos.pasos(), estados.append, **opciones
    )


def confirmacion(*hablantes):
    return c.Confirmacion(
        etiquetas=[{"hablante": h, "etiqueta": "femenino", "origen": "persona"} for h in hablantes]
    )


# --- Fase 1: hasta «esperando confirmación» ------------------------------------------------


def test_fase_1_recorre_los_pasos_en_orden(tmp_path):
    falsos, estados = Falsos(), []
    fase_1(tmp_path, falsos, estados)
    assert falsos.llamadas == ["preparar", "diarizar", "proponer_voz", "elegir_fragmentos"]


def test_fase_1_acaba_esperando_confirmacion(tmp_path):  # RF-04, RF-07
    estados = []
    preparado = fase_1(tmp_path, Falsos(), estados)
    assert preparado is not None
    assert estados[-1].estado is c.Estado.ESPERANDO_CONFIRMACION
    assert all(e.estado is c.Estado.PROCESANDO for e in estados[:-1])
    assert all(e.id_analisis == ID for e in estados)


def test_el_progreso_avanza_entre_0_y_100(tmp_path):  # RF-04
    estados = []
    fase_1(tmp_path, Falsos(), estados)
    progresos = [e.progreso for e in estados if e.estado is c.Estado.PROCESANDO]
    assert progresos == sorted(progresos)
    assert all(0 <= x <= 100 for x in progresos)


def test_el_wav_tiene_un_nombre_generado_por_el_sistema(tmp_path):  # RNF-10
    falsos = Falsos()
    fase_1(tmp_path, falsos, [])
    assert falsos.destino == tmp_path / f"{ID}.wav"


def test_solo_pasan_a_confirmar_las_voces_presentes(tmp_path):  # RN-01
    preparado = fase_1(tmp_path, Falsos(), [])
    hablantes = preparado.hablantes.hablantes
    assert [h.hablante for h in hablantes] == [1, 2]
    assert [h.segundos_habla for h in hablantes] == [20.0, 20.5]


def test_cada_voz_lleva_su_propuesta_y_sus_fragmentos(tmp_path):  # RF-06, RF-07
    preparado = fase_1(tmp_path, Falsos(), [])
    h1, h2 = preparado.hablantes.hablantes
    assert h1.propuesta == PROPUESTAS[1] and h1.fragmentos == FRAGMENTOS[1]
    assert h2.propuesta == PROPUESTAS[2] and h2.fragmentos == FRAGMENTOS[2]


def test_se_guardan_todos_los_turnos_para_el_analisis(tmp_path):
    preparado = fase_1(tmp_path, Falsos(), [])
    assert preparado.duracion == DURACION
    assert preparado.turnos == TURNOS
    assert preparado.solapamientos == SOLAPAMIENTOS


def test_modo_manual_no_ejecuta_el_clasificador(tmp_path):  # RF-08
    falsos = Falsos()
    preparado = fase_1(tmp_path, falsos, [], modo_manual=True)
    assert "proponer_voz" not in falsos.llamadas
    assert all(h.propuesta is None for h in preparado.hablantes.hablantes)


def test_falta_una_propuesta_en_modo_asistido(tmp_path):  # RF-06: una por hablante
    estados = []
    falsos = Falsos(propuestas={1: PROPUESTAS[1]})
    assert fase_1(tmp_path, falsos, estados) is None
    assert estados[-1].estado is c.Estado.ERROR
    assert "Hablante 2" in estados[-1].motivo_error


@pytest.mark.parametrize("paso", ["preparar", "diarizar", "proponer_voz", "elegir_fragmentos"])
def test_si_un_paso_falla_acaba_en_error_con_motivo(tmp_path, paso):  # RNF-16
    estados = []
    falsos = Falsos(falla=paso)
    assert fase_1(tmp_path, falsos, estados) is None
    assert estados[-1].estado is c.Estado.ERROR
    assert "roto" in estados[-1].motivo_error
    assert falsos.llamadas[-1] == paso  # no sigue con los pasos siguientes


# --- Fase 2: tras la confirmación humana ---------------------------------------------------


def test_fase_2_analiza_y_termina(tmp_path):  # RF-04, RF-07
    falsos, estados = Falsos(), []
    preparado = fase_1(tmp_path, falsos, [])
    conf = confirmacion(1, 2)
    resultado = p.analizar_confirmado(ID, preparado, conf, falsos.pasos(), estados.append)
    assert resultado.id_analisis == ID
    assert estados[0].estado is c.Estado.PROCESANDO
    assert estados[-1].estado is c.Estado.TERMINADO
    assert falsos.entrada.etiquetas == conf.etiquetas
    assert falsos.entrada.turnos == TURNOS
    assert falsos.entrada.duracion == DURACION


@pytest.mark.parametrize("hablantes", [(1,), (1, 2, 3)])
def test_la_confirmacion_debe_cubrir_justo_las_voces_presentes(tmp_path, hablantes):  # RF-07
    falsos, estados = Falsos(), []
    preparado = fase_1(tmp_path, falsos, [])
    with pytest.raises(p.ConfirmacionInvalida):
        p.analizar_confirmado(
            ID, preparado, confirmacion(*hablantes), falsos.pasos(), estados.append
        )
    assert "analizar" not in falsos.llamadas
    assert estados == []  # es un error de quien confirma: el análisis no cambia de estado


def test_si_el_analisis_falla_acaba_en_error(tmp_path):  # RNF-16
    falsos, estados = Falsos(falla="analizar"), []
    preparado = fase_1(tmp_path, falsos, [])
    resultado = p.analizar_confirmado(
        ID, preparado, confirmacion(1, 2), falsos.pasos(), estados.append
    )
    assert resultado is None
    assert estados[-1].estado is c.Estado.ERROR
    assert "roto" in estados[-1].motivo_error
