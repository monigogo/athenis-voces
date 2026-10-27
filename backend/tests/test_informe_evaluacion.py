"""Pruebas de evaluacion/informe_evaluacion.ipynb (T031): regenera la tabla de 12.1 con evaluar.py."""

import json
import os
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
CUADERNO = RAIZ / "evaluacion" / "informe_evaluacion.ipynb"


@pytest.fixture
def cuaderno():
    return json.loads(CUADERNO.read_text(encoding="utf-8"))


def celdas_de_codigo(cuaderno):
    return [c for c in cuaderno["cells"] if c["cell_type"] == "code"]


def test_es_un_cuaderno_de_jupyter(cuaderno):
    assert cuaderno["nbformat"] == 4
    assert celdas_de_codigo(cuaderno)


def test_se_guarda_sin_resultados(cuaderno):  # las cifras salen al ejecutarlo, no del repositorio
    for celda in celdas_de_codigo(cuaderno):
        assert celda["outputs"] == []
        assert celda["execution_count"] is None


def test_regenera_la_tabla_con_evaluar_py(cuaderno, tmp_path, monkeypatch):  # FR-015, RNF-07
    pytest.importorskip("pyannote.metrics")
    for carpeta in ("salidas", "ami", "etiquetas"):
        (tmp_path / carpeta).mkdir()
    monkeypatch.setenv("SALIDAS", str(tmp_path / "salidas"))
    monkeypatch.setenv("AMI", str(tmp_path / "ami"))
    monkeypatch.setenv("ETIQUETAS", str(tmp_path / "etiquetas"))
    monkeypatch.chdir(RAIZ / "evaluacion")

    espacio: dict = {}
    for celda in celdas_de_codigo(cuaderno):
        exec("".join(celda["source"]), espacio)  # noqa: S102 (código del propio repositorio)

    assert "| M-01, DER (reuniones de AMI)" in espacio["tabla"]
    assert "| M-09" in espacio["tabla"]
    assert os.environ["SALIDAS"] in espacio["orden"]
