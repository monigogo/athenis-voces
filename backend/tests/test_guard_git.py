"""Pruebas del hook .claude/hooks/guard-git.sh: bloquea lo que prohíben las reglas de contribución."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "guard-git.sh"

pytestmark = pytest.mark.skipif(shutil.which("jq") is None, reason="el hook necesita jq")


def codigo(orden: str, entorno: dict | None = None) -> int:
    entrada = json.dumps({"tool_input": {"command": orden}})
    return subprocess.run(
        ["bash", str(HOOK)],
        input=entrada,
        capture_output=True,
        text=True,
        check=False,
        env=entorno,
    ).returncode


@pytest.fixture
def sin_jq(tmp_path):
    """Un PATH con lo que usa el hook (bash, grep, sed, cat), pero sin jq."""
    for programa in ("bash", "grep", "sed", "cat"):
        (tmp_path / programa).symlink_to(shutil.which(programa))
    return {"PATH": str(tmp_path)}


@pytest.mark.parametrize(
    "orden",
    [
        "git push --force origin rama",
        "git push -f origin rama",
        "git push --force-with-lease origin rama",  # CONTRIBUTING: nunca se fuerza
        "git push -uf origin rama",  # -f junto a otras opciones
        "git push origin +rama",  # el + delante de la rama también fuerza
        "git commit -m 'Co-Authored-By: alguien'",
        "git push origin develop",
        "git push origin main",
        "git add .env",
    ],
)
def test_bloquea(orden):
    assert codigo(orden) == 2


@pytest.mark.parametrize(
    "orden",
    [
        "git push -u origin feat/moni/x",
        "git add .env.example",
        "git status",
        # la regla de la IA mira el mensaje del commit, no el nombre de los ficheros
        "git add docs/claude-notas.md && git commit -m 'docs: notas'",
    ],
)
def test_deja_pasar(orden):
    assert codigo(orden) == 0


def test_sin_jq_tambien_bloquea(sin_jq):  # sin jq, antes dejaba pasar todo
    assert codigo("git push --force origin rama", sin_jq) == 2


def test_sin_jq_deja_pasar_lo_normal(sin_jq):  # y no bloquea cualquier orden
    assert codigo("ls -la", sin_jq) == 0


def test_sin_jq_tampoco_deja_subir_un_env(sin_jq):  # la orden se saca bien del JSON
    assert codigo("git add .env", sin_jq) == 2
