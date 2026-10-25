"""Pruebas de evaluacion/cronometrar.py: minutos de proceso por hora de audio (M-09, T024)."""

import pytest

from evaluacion import cronometrar


def test_una_hora_procesada_en_15_minutos_da_15():  # RNF-01
    assert cronometrar.minutos_por_hora(duracion_audio=3600.0, segundos=900.0) == 15.0


def test_media_hora_procesada_en_3_minutos_da_6():
    assert cronometrar.minutos_por_hora(duracion_audio=1800.0, segundos=180.0) == 6.0


def test_sin_duracion_no_se_aplica():  # RN-13
    assert cronometrar.minutos_por_hora(duracion_audio=0.0, segundos=10.0) is None


def test_guardar_y_leer_los_tiempos(tmp_path):
    cronometrar.guardar(tmp_path / "b.tiempo.json", duracion_audio=3600.0, segundos=360.0)
    cronometrar.guardar(tmp_path / "a.tiempo.json", duracion_audio=1800.0, segundos=360.0)
    (tmp_path / "a.json").write_text("{}", encoding="utf-8")  # el Resultado no es un tiempo
    assert cronometrar.leer(tmp_path) == [12.0, 6.0]  # por orden de nombre: a, b


def test_sin_tiempos_guardados_no_hay_nada(tmp_path):
    assert cronometrar.leer(tmp_path) == []


def test_el_fichero_guarda_lo_medido(tmp_path):
    ruta = tmp_path / "x.tiempo.json"
    cronometrar.guardar(ruta, duracion_audio=60.0, segundos=6.5)
    assert cronometrar.leer_uno(ruta) == pytest.approx((60.0, 6.5))
