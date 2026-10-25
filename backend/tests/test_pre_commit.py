"""Pruebas de los hooks de pre-commit (B06): gitleaks, ruff y Biome, y cada uno en su carpeta."""

import re
import tomllib
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / ".pre-commit-config.yaml"


@pytest.fixture(scope="module")
def hooks():
    """Los hooks de la configuración, por id, junto al repositorio de donde salen."""
    repos = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["repos"]
    return {h["id"]: (r["repo"], r["rev"], h) for r in repos for h in r["hooks"]}


def test_estan_los_tres_del_plan(hooks):  # B06
    assert {"gitleaks", "ruff-check", "ruff-format", "biome-ci"} <= set(hooks)


def test_gitleaks_mira_todo_el_repositorio(hooks):  # RD-04: claves nunca
    _, _, hook = hooks["gitleaks"]
    assert "files" not in hook and "exclude" not in hook


@pytest.mark.parametrize("id_", ["ruff-check", "ruff-format"])
def test_ruff_solo_mira_el_backend(hooks, id_):  # constitución 5
    assert hooks[id_][2]["files"] == r"^backend/"


def test_biome_solo_mira_el_frontend_y_sin_modificar_nada(hooks):  # constitución 5
    _, _, hook = hooks["biome-ci"]
    assert hook["files"] == r"^frontend/"
    assert "--write" not in hook.get("entry", "")


def test_las_revisiones_estan_fijadas(hooks):  # 11.4: versiones fijas
    for repo, rev, _ in hooks.values():
        assert re.fullmatch(r"v\d+\.\d+\.\d+", rev), repo


def test_ruff_es_el_mismo_que_el_del_backend(hooks):  # un solo ruff: el del uv.lock
    bloqueados = tomllib.loads((RAIZ / "backend" / "uv.lock").read_text(encoding="utf-8"))
    version = next(p["version"] for p in bloqueados["package"] if p["name"] == "ruff")
    assert hooks["ruff-check"][1] == f"v{version}"
    assert hooks["ruff-format"][1] == f"v{version}"
