"""Pruebas del registro de análisis y de la cola del servidor (spec 003, fase 2)."""

import pytest
from conftest import INICIO, EjecutorSincrono, PasosQueEscriben

import contrato as c
from api.cola import Cola
from api.registro import Analisis, AnalisisDesconocido, Registro


def nuevo(id_analisis="a1", audio=None):
    return Analisis(
        id_analisis=id_analisis,
        creado_en=INICIO,
        estado=c.EstadoAnalisis(id_analisis=id_analisis, estado=c.Estado.EN_COLA),
        audio=audio,
    )


def test_crear_y_obtener():
    registro = Registro()
    registro.crear(nuevo())
    assert registro.obtener("a1").estado.estado is c.Estado.EN_COLA


def test_un_id_desconocido_da_su_error():
    with pytest.raises(AnalisisDesconocido):
        Registro().obtener("no-existe")


def test_guarda_el_ultimo_estado_notificado():
    registro = Registro()
    registro.crear(nuevo())
    registro.notificar(c.EstadoAnalisis(id_analisis="a1", estado="procesando", progreso=25.0))
    assert registro.obtener("a1").estado.progreso == 25.0


def test_lista_todos():
    registro = Registro()
    registro.crear(nuevo("a1"))
    registro.crear(nuevo("a2"))
    assert sorted(a.id_analisis for a in registro.todos()) == ["a1", "a2"]


def test_la_fase_1_deja_lo_preparado_y_espera_confirmacion(tmp_path):
    registro, falsos = Registro(), PasosQueEscriben()
    registro.crear(nuevo(audio=tmp_path / "a1.subida"))
    Cola(registro, falsos.pasos(), tmp_path, EjecutorSincrono()).fase1("a1")
    analisis = registro.obtener("a1")
    assert analisis.estado.estado is c.Estado.ESPERANDO_CONFIRMACION
    assert analisis.preparado is not None
    assert analisis.wav == tmp_path / "a1.wav"
    assert analisis.wav.exists()


def test_esperando_confirmacion_solo_se_ve_con_lo_preparado_ya_guardado(tmp_path):
    """Si alguien pregunta en cuanto ve el estado, los hablantes ya tienen que estar."""
    registro, falsos = Registro(), PasosQueEscriben()
    registro.crear(nuevo(audio=tmp_path / "a1.subida"))
    vistos = []
    original = registro.notificar

    def mirar(estado):
        original(estado)
        vistos.append((estado.estado, registro.obtener("a1").preparado is not None))

    registro.notificar = mirar
    Cola(registro, falsos.pasos(), tmp_path, EjecutorSincrono()).fase1("a1")
    assert (c.Estado.ESPERANDO_CONFIRMACION, True) in vistos
    assert (c.Estado.ESPERANDO_CONFIRMACION, False) not in vistos


def test_un_fallo_inesperado_acaba_en_error_y_no_cuelga(tmp_path):
    registro = Registro()
    registro.crear(nuevo(audio=tmp_path / "a1.subida"))
    cola = Cola(registro, None, tmp_path, EjecutorSincrono())  # sin pasos: falla al empezar
    cola.fase1("a1")
    estado = registro.obtener("a1").estado
    assert estado.estado is c.Estado.ERROR
    assert estado.motivo_error


def test_la_fase_2_deja_el_resultado_terminado(tmp_path):
    registro, falsos = Registro(), PasosQueEscriben()
    registro.crear(nuevo(audio=tmp_path / "a1.subida"))
    cola = Cola(registro, falsos.pasos(), tmp_path, EjecutorSincrono())
    cola.fase1("a1")
    confirmacion = c.Confirmacion(
        etiquetas=[
            c.EtiquetaConfirmada(hablante=h, etiqueta="indeterminado", origen="persona")
            for h in (1, 2)
        ]
    )
    cola.fase2("a1", confirmacion)
    analisis = registro.obtener("a1")
    assert analisis.estado.estado is c.Estado.TERMINADO
    assert analisis.resultado.id_analisis == "a1"
