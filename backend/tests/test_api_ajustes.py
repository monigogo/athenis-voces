"""Pruebas de los ajustes del servidor, que llegan del entorno (spec 003)."""

import tempfile
from pathlib import Path

from api.ajustes import EJEMPLOS_POR_DEFECTO, desde_entorno

REPOSITORIO = Path(__file__).resolve().parents[2]


def test_valores_por_defecto():
    ajustes = desde_entorno({})
    assert ajustes.carpeta_trabajo == Path(tempfile.gettempdir()) / "athenis-voces"
    assert ajustes.ejemplos == EJEMPLOS_POR_DEFECTO
    assert ajustes.demo_publica is False


def test_la_carpeta_de_trabajo_por_defecto_no_esta_en_el_repositorio():  # RD-04
    assert not desde_entorno({}).carpeta_trabajo.resolve().is_relative_to(REPOSITORIO)


def test_los_ejemplos_por_defecto_no_salen_de_las_pruebas():
    assert EJEMPLOS_POR_DEFECTO == REPOSITORIO / "backend" / "ejemplos"


def test_desde_el_entorno(tmp_path):
    ajustes = desde_entorno(
        {
            "CARPETA_TRABAJO": str(tmp_path / "t"),
            "EJEMPLOS_DIR": str(tmp_path / "e"),
            "DEMO_PUBLICA": "1",
        }
    )
    assert ajustes.carpeta_trabajo == tmp_path / "t"
    assert ajustes.ejemplos == tmp_path / "e"
    assert ajustes.demo_publica is True


def test_demo_publica_solo_con_un_valor_afirmativo():
    for valor, esperado in [("true", True), ("SI", True), ("0", False), ("no", False), ("", False)]:
        assert desde_entorno({"DEMO_PUBLICA": valor}).demo_publica is esperado
