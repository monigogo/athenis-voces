"""Pruebas de scripts/revisar_seguridad.sh (RNF-09) y scripts/listar_licencias.sh (RNF-18).

Con gitleaks, uv y pnpm falsos: sin red, y cada prueba decide qué encuentran.
"""

import os
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
SEGURIDAD = RAIZ / "scripts" / "revisar_seguridad.sh"
LICENCIAS = RAIZ / "scripts" / "listar_licencias.sh"

# Cada falso apunta cómo lo llaman y sale con el código que diga su variable de entorno
FALSO = """#!/usr/bin/env bash
echo "{nombre} $*" >> "$LLAMADAS"
case " $* " in
  *" pip-audit "*) exit "${{PIP_AUDIT:-0}}" ;;
  *" bandit "*) exit "${{BANDIT:-0}}" ;;
  *" pip-licenses "*) echo '[{{"Name": "paquete", "Version": "1.0", "License": "MIT License"}}]' ;;
  *"comprobar_licencias.py "*) cat "${{@: -1}}"; exit "${{COMPROBAR:-0}}" ;;
  *" export "*) echo "paquete==1.0" ;;
  *" licenses "*) printf '%s\\n' "${{PNPM_TEXTO:-react MIT}}" ;;
  *" audit "*) exit "${{PNPM_AUDIT:-0}}" ;;
esac
[ "{nombre}" = gitleaks ] && exit "${{GITLEAKS:-0}}"
exit 0
"""


@pytest.fixture
def entorno(tmp_path):
    falsos = tmp_path / "bin"
    falsos.mkdir()
    for nombre in ("gitleaks", "uv", "pnpm"):
        (falsos / nombre).write_text(FALSO.format(nombre=nombre), encoding="utf-8", newline="\n")
        (falsos / nombre).chmod(0o755)
    sin_web = tmp_path / "sin_web"
    sin_web.mkdir()
    return {
        "PATH": f"{falsos}{os.pathsep}{os.environ['PATH']}",
        "LLAMADAS": str(tmp_path / "llamadas.txt"),
        "FRONTEND": str(sin_web),
    }


def ejecutar(script, entorno, **variables):
    env = {**os.environ, **entorno, **variables}
    resultado = subprocess.run(
        ["bash", str(script)], capture_output=True, text=True, env=env, check=False
    )
    llamadas = Path(entorno["LLAMADAS"])
    texto = llamadas.read_text(encoding="utf-8") if llamadas.exists() else ""
    return resultado, texto


def con_web(entorno, tmp_path):
    web = tmp_path / "web"
    web.mkdir()
    (web / "package.json").write_text("{}", encoding="utf-8")
    return {**entorno, "FRONTEND": str(web)}


# --- revisar_seguridad.sh ------------------------------------------------------------------


def test_seguridad_sin_problemas_acaba_bien(entorno):
    resultado, _ = ejecutar(SEGURIDAD, entorno)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "0 problemas graves" in resultado.stdout


def test_busca_claves_en_todo_el_historial(entorno):  # RD-04, 12.3
    _, llamadas = ejecutar(SEGURIDAD, entorno)
    assert "gitleaks git" in llamadas
    assert "--redact" in llamadas  # el informe no muestra la clave


def test_busca_fallos_conocidos_en_las_librerias_de_todos_los_grupos(entorno):
    _, llamadas = ejecutar(SEGURIDAD, entorno)
    assert "uv export" in llamadas and "--all-groups" in llamadas
    assert "pip-audit" in llamadas


def test_busca_codigo_peligroso_de_gravedad_alta(entorno):
    _, llamadas = ejecutar(SEGURIDAD, entorno)
    linea = next(x for x in llamadas.splitlines() if "bandit" in x)
    assert "-lll" in linea  # solo gravedad alta (RNF-09)
    assert "src" in linea and "scripts" in linea


@pytest.mark.parametrize("variable", ["GITLEAKS", "PIP_AUDIT", "BANDIT"])
def test_cualquier_problema_grave_hace_fallar_la_revision(entorno, variable):  # RNF-09
    resultado, _ = ejecutar(SEGURIDAD, entorno, **{variable: "1"})
    assert resultado.returncode == 1
    assert "problema grave" in resultado.stdout


def test_sin_web_no_se_revisa_la_web(entorno):
    _, llamadas = ejecutar(SEGURIDAD, entorno)
    assert "pnpm" not in llamadas


def test_con_web_se_revisan_sus_librerias(entorno, tmp_path):
    resultado, llamadas = ejecutar(SEGURIDAD, con_web(entorno, tmp_path), PNPM_AUDIT="1")
    assert "pnpm audit --audit-level high" in llamadas
    assert resultado.returncode == 1


def test_sin_gitleaks_no_se_da_por_buena(entorno, tmp_path):
    """Si una herramienta no está, la revisión no puede decir que todo va bien."""
    resultado, _ = ejecutar(SEGURIDAD, entorno, GITLEAKS_BIN=str(tmp_path / "no_existe"))
    assert resultado.returncode == 1
    assert "gitleaks" in resultado.stdout


# --- listar_licencias.sh -------------------------------------------------------------------


def test_licencias_abiertas_acaba_bien_y_las_lista(entorno):
    resultado, llamadas = ejecutar(LICENCIAS, entorno)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "MIT License" in resultado.stdout
    linea = next(x for x in llamadas.splitlines() if "pip-licenses" in x)
    assert "--all-groups" in linea  # también audio y evaluacion: es lo que se entrega
    assert "--with-license-file" in linea  # para decidir las que no declaran su licencia


def test_falla_si_alguna_licencia_no_es_abierta(entorno):  # RNF-18
    _, llamadas = ejecutar(LICENCIAS, entorno)
    assert "comprobar_licencias.py" in llamadas
    resultado, _ = ejecutar(LICENCIAS, entorno, COMPROBAR="1")
    assert resultado.returncode == 1


def test_lista_tambien_las_licencias_de_la_web(entorno, tmp_path):
    resultado, llamadas = ejecutar(LICENCIAS, con_web(entorno, tmp_path))
    assert "pnpm licenses list --prod" in llamadas
    assert "react MIT" in resultado.stdout


def test_falla_si_una_libreria_de_la_web_no_es_abierta(entorno, tmp_path):
    resultado, _ = ejecutar(LICENCIAS, con_web(entorno, tmp_path), PNPM_TEXTO="sdk Proprietary")
    assert resultado.returncode == 1


def test_solo_se_ignoran_los_fallos_aceptados_en_d20(entorno):  # anexo C, D-20
    _, llamadas = ejecutar(SEGURIDAD, entorno)
    linea = next(x for x in llamadas.splitlines() if "pip-audit" in x)
    partes = linea.split()
    ignorados = [partes[i + 1] for i, p in enumerate(partes) if p == "--ignore-vuln"]
    assert sorted(ignorados) == ["GHSA-xmj3-9gf7-h52w", "PYSEC-2026-3447"]


def test_un_solo_problema_se_dice_en_singular(entorno):
    resultado, _ = ejecutar(SEGURIDAD, entorno, BANDIT="1")
    assert "Resultado: 1 problema grave." in resultado.stdout
