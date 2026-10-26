"""Pruebas de backend/scripts/comprobar_licencias.py (RNF-18): decide si cada licencia es abierta."""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "comprobar_licencias.py"


@pytest.fixture
def mod():
    spec = importlib.util.spec_from_file_location("comprobar_licencias", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.mark.parametrize(
    "licencia",
    [
        "MIT",
        "MIT License",
        "Apache-2.0",
        "Apache Software License",
        "BSD-3-Clause",
        "Python Software Foundation License",
        "Mozilla Public License 2.0 (MPL 2.0)",
        "BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0",
        "GNU Lesser General Public License v2 or later (LGPLv2+)",
    ],
)
def test_licencias_abiertas(mod, licencia):
    assert mod.estado(licencia, "") == mod.ABIERTA


@pytest.mark.parametrize("licencia", ["NVIDIA Proprietary Software", "Other/Proprietary License"])
def test_licencias_que_no_son_abiertas(mod, licencia):
    assert mod.estado(licencia, "") == mod.NO_ABIERTA


def test_sin_licencia_declarada_se_mira_su_fichero(mod):  # caso de pyannote-core
    assert mod.estado("UNKNOWN", "The MIT License (MIT)\n\nCopyright (c) 2014 CNRS") == (
        mod.ABIERTA_SEGUN_FICHERO
    )


def test_un_fichero_privativo_no_se_da_por_abierto(mod):
    texto = "NVIDIA Software License Agreement. This is a proprietary license."
    assert mod.estado("UNKNOWN", texto) == mod.NO_ABIERTA


def test_si_no_se_sabe_no_se_da_por_buena(mod):
    assert mod.estado("UNKNOWN", "") == mod.NO_CONSTA


def test_main_lista_y_falla_si_alguna_no_es_abierta(mod, tmp_path, capsys):
    paquetes = [
        {"Name": "pydantic", "Version": "2.0", "License": "MIT", "LicenseText": ""},
        {"Name": "nvidia-x", "Version": "1.0", "License": "NVIDIA Proprietary Software"},
    ]
    ruta = tmp_path / "licencias.json"
    ruta.write_text(json.dumps(paquetes), encoding="utf-8")
    assert mod.main([str(ruta)]) == 1
    salida = capsys.readouterr().out
    assert "| pydantic | 2.0 | MIT | abierta |" in salida
    assert "| nvidia-x | 1.0 | NVIDIA Proprietary Software | NO abierta |" in salida
    assert "1 de 2" in salida


def test_main_acaba_bien_si_todas_son_abiertas(mod, tmp_path):
    ruta = tmp_path / "licencias.json"
    ruta.write_text(json.dumps([{"Name": "a", "Version": "1", "License": "MIT"}]), "utf-8")
    assert mod.main([str(ruta)]) == 0


def test_apache_no_se_confunde_por_hablar_de_danos_comerciales(mod):
    texto = (
        "Apache License\nVersion 2.0, January 2004\n\n" + "x\n" * 50 + "other commercial damages"
    )
    assert mod.estado("UNKNOWN", texto) == mod.ABIERTA_SEGUN_FICHERO


# --- D-22: las librerías CUDA de NVIDIA, solo para usar la GPU que cede OVHcloud ---------------


@pytest.mark.parametrize(
    ("nombre", "licencia"),
    [
        ("nvidia-cublas-cu12", "Other/Proprietary License"),
        ("nvidia-nccl-cu12", "LicenseRef-NVIDIA-Proprietary"),
        ("nvidia-cusparselt-cu12", "NVIDIA Proprietary Software"),
        ("cuda-toolkit", "UNKNOWN"),
    ],
)
def test_las_librerias_cuda_estan_permitidas_por_d22(mod, nombre, licencia):
    assert mod.estado(licencia, "", nombre) == mod.PERMITIDA


@pytest.mark.parametrize("nombre", ["nvidia-x", "otra-cosa-cu12", "sdk-cerrado"])
def test_la_excepcion_no_vale_para_otros_paquetes(mod, nombre):
    assert mod.estado("NVIDIA Proprietary Software", "", nombre) == mod.NO_ABIERTA


def test_main_no_falla_por_las_librerias_cuda_pero_las_lista(mod, tmp_path, capsys):
    paquetes = [
        {"Name": "pydantic", "Version": "2.0", "License": "MIT"},
        {"Name": "nvidia-cublas-cu12", "Version": "12.6", "License": "Other/Proprietary License"},
    ]
    ruta = tmp_path / "licencias.json"
    ruta.write_text(json.dumps(paquetes), encoding="utf-8")
    assert mod.main([str(ruta)]) == 0
    salida = capsys.readouterr().out
    assert "| nvidia-cublas-cu12 | 12.6 | Other/Proprietary License | permitida (D-22) |" in salida
    assert "1 de 2 paquetes con licencia cerrada permitida por D-22" in salida
