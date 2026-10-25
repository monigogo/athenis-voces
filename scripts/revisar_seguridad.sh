#!/usr/bin/env bash
# Revisión de seguridad antes de entregar (RNF-09): falla si encuentra algo grave.
#
# Uso, desde la raíz del repositorio:   scripts/revisar_seguridad.sh
#
# 1. Claves en todo el historial de git (gitleaks; RD-04). El informe no muestra la clave.
# 2. Librerías del backend con fallos de seguridad conocidos (pip-audit), de todos los grupos.
# 3. Código Python peligroso de gravedad alta (bandit).
# 4. Librerías de la web con fallos de gravedad alta (pnpm audit), si la web existe.
# Si falta una herramienta, la revisión falla: no se puede dar por buena sin mirarlo.
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND="${FRONTEND:-$RAIZ/frontend}"
problemas=0

# Fallos conocidos aceptados (anexo C, D-20). PyTorch 2.11.0, el que funciona en la V100S, exige
# setuptools < 82, y estos dos fallos de setuptools 81 no nos afectan:
#   PYSEC-2026-3447: solo al empaquetar una distribución de código fuente en macOS.
#   GHSA-xmj3-9gf7-h52w: solo al instalar un wheel a la antigua (como egg) en Windows.
ACEPTADOS=(PYSEC-2026-3447 GHSA-xmj3-9gf7-h52w)
ignorar=()
for id in "${ACEPTADOS[@]}"; do ignorar+=(--ignore-vuln "$id"); done

fallo() {
  echo "PROBLEMA: $1"
  problemas=$((problemas + 1))
}

# gitleaks llega con los hooks de pre-commit (uv run pre-commit install)
GITLEAKS_BIN="${GITLEAKS_BIN:-$(command -v gitleaks || find "$HOME/.cache/pre-commit" -path '*golangenv*/bin/gitleaks' -type f 2>/dev/null | head -1)}"

echo "== 1. Claves en el historial de git"
if [ -x "$GITLEAKS_BIN" ]; then
  "$GITLEAKS_BIN" git "$RAIZ" --redact --no-banner || fallo "gitleaks ha encontrado claves"
else
  fallo "no está gitleaks: instala los hooks con 'uv run pre-commit install' desde backend/"
fi

echo "== 2. Librerías del backend con fallos conocidos"
requisitos="$(mktemp)"
trap 'rm -f "$requisitos"' EXIT
if (cd "$RAIZ/backend" && uv export --frozen --all-groups --no-hashes --no-emit-project >"$requisitos"); then
  (cd "$RAIZ/backend" && uv run pip-audit -r "$requisitos" --no-deps --disable-pip "${ignorar[@]}") \
    || fallo "pip-audit ha encontrado librerías con fallos de seguridad"
  echo "Nota: torch y torchaudio vienen del índice de PyTorch y pip-audit no los puede revisar."
else
  fallo "no se han podido listar las librerías del backend"
fi

echo "== 3. Código Python peligroso (gravedad alta)"
(cd "$RAIZ/backend" && uv run bandit -r src scripts -lll -q) \
  || fallo "bandit ha encontrado código de gravedad alta"

if [ -f "$FRONTEND/package.json" ]; then
  echo "== 4. Librerías de la web con fallos de gravedad alta"
  (cd "$FRONTEND" && pnpm audit --audit-level high) \
    || fallo "pnpm audit ha encontrado librerías de la web con fallos graves"
fi

echo
if [ "$problemas" -eq 0 ]; then
  echo "Resultado: 0 problemas graves."
elif [ "$problemas" -eq 1 ]; then
  echo "Resultado: 1 problema grave. Hay que arreglarlo antes de entregar (RNF-09)."
  exit 1
else
  echo "Resultado: $problemas problemas graves. Hay que arreglarlos antes de entregar (RNF-09)."
  exit 1
fi
