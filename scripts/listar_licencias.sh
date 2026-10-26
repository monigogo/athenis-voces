#!/usr/bin/env bash
# Inventario de licencias de las dependencias (RNF-18): las lista y falla si alguna no es abierta.
#
# Uso, desde la raíz del repositorio:   scripts/listar_licencias.sh
#
# El backend se lista con todos sus grupos (también audio y evaluacion), porque es lo que se entrega:
# la primera vez instala los modelos y tarda. La web, solo si existe.
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND="${FRONTEND:-$RAIZ/frontend}"
problemas=0

echo "== Backend"
lista="$(mktemp)"
trap 'rm -f "$lista"' EXIT
# Con el texto de cada licencia: algunos paquetes (pyannote) no la declaran y solo traen el fichero
if (cd "$RAIZ/backend" && uv run --all-groups pip-licenses --from=mixed --with-license-file \
  --no-license-path --format=json >"$lista"); then
  (cd "$RAIZ/backend" && uv run python scripts/comprobar_licencias.py "$lista") \
    || { echo "PROBLEMA: hay licencias del backend que no son abiertas o no constan"; problemas=1; }
else
  echo "PROBLEMA: no se han podido listar las licencias del backend"
  problemas=1
fi

if [ -f "$FRONTEND/package.json" ]; then
  echo "== Web"
  web="$(cd "$FRONTEND" && pnpm licenses list --prod)" \
    || { echo "PROBLEMA: no se han podido listar las licencias de la web"; problemas=1; }
  echo "$web"
  if grep -Eqi "proprietary|commercial|unknown" <<<"$web"; then
    echo "PROBLEMA: hay licencias de la web que no son abiertas o no constan"
    problemas=1
  fi
fi

exit "$problemas"
