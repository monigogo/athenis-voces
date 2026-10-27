"""Los pasos reales del servidor son los módulos de las features 001 y 002 (spec 003, T024)."""

from analisis.analizar import analizar
from api.pasos_reales import pasos_reales
from audio.diarizacion import diarizar
from audio.fragmentos import elegir_fragmentos
from audio.preparar import preparar
from voz.clasificador import proponer_voz


def test_usa_los_modulos_reales():
    pasos = pasos_reales()
    assert pasos.preparar is preparar
    assert pasos.diarizar is diarizar
    assert pasos.proponer_voz is proponer_voz
    assert pasos.elegir_fragmentos is elegir_fragmentos
    assert pasos.analizar is analizar
