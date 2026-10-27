"""Pruebas del hook .claude/hooks/guard-git.sh: bloquea lo que prohíben las reglas de contribución."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "guard-git.sh"

pytestmark = pytest.mark.skipif(shutil.which("jq") is None, reason="el hook necesita jq")


def codigo(orden: str) -> int:
    entrada = json.dumps({"tool_input": {"command": orden}})
    return subprocess.run(
        ["bash", str(HOOK)], input=entrada, capture_output=True, text=True, check=False
    ).returncode


@pytest.mark.parametrize(
    "orden",
    [
        "git push --force origin rama",
        "git push -f origin rama",
        "git push --force-with-lease origin rama",  # CONTRIBUTING: nunca se fuerza
        "git push origin develop",
        "git push origin main",
        "git add .env",
    ],
)
def test_bloquea(orden):
    assert codigo(orden) == 2


@pytest.mark.parametrize(
    "orden", ["git push -u origin feat/moni/x", "git add .env.example", "git status"]
)
def test_deja_pasar(orden):
    assert codigo(orden) == 0
