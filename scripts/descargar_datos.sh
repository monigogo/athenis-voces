#!/usr/bin/env bash
# Descarga los datos de evaluación (A09; constitución, regla 7): las 7 reuniones de AMI y las
# anotaciones de BUT. Nada de esto entra en el repositorio: datos/ está en .gitignore (RD-04).
#
# Uso, desde la raíz del repositorio:   scripts/descargar_datos.sh [carpeta]
# Por defecto, en datos/ami. Se puede repetir: lo que ya está bien no se vuelve a bajar.
#
# Licencias y citas: docs/datos.md. Desarrollo: IB4002 e IB4010. Prueba, solo para medir
# (regla 9): EN2002a, EN2002c, ES2004a, IS1009a y TS3003a (funcional, 11.3).
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DESTINO="${1:-$RAIZ/datos/ami}"
SUMAS="${SUMAS:-$RAIZ/scripts/ami.sha256}"  # huella de cada audio, para saber que llega entero

AMI_URL="https://groups.inf.ed.ac.uk/ami/AMICorpusMirror/amicorpus"
BUT_REPO="https://github.com/BUTSpeechFIT/AMI-diarization-setup.git"
BUT_COMMIT="2509d8933721023fab4def2618aabd5c28eb82e9"

suma_esperada() {
  awk -v f="$1" '$2 == f { print $1 }' "$SUMAS"
}

suma_de() {
  sha256sum "$1" | cut -d' ' -f1
}

descargar_audio() {
  local fichero="$1.Mix-Headset.wav"
  local destino="$DESTINO/audios/$fichero"
  local esperada
  esperada="$(suma_esperada "$fichero")"
  if [ -z "$esperada" ]; then
    echo "Falta la suma de $fichero en $SUMAS" >&2
    return 1
  fi
  if [ -f "$destino" ] && [ "$(suma_de "$destino")" = "$esperada" ]; then
    echo "Ya está: $fichero"
    return 0
  fi
  echo "Descargando $fichero"
  curl -fsSL --retry 3 -o "$destino.parcial" "$AMI_URL/$1/audio/$fichero"
  if [ "$(suma_de "$destino.parcial")" != "$esperada" ]; then
    rm -f "$destino.parcial"
    echo "La huella de $fichero no coincide: no se guarda. Vuelve a intentarlo más tarde." >&2
    return 1
  fi
  mv "$destino.parcial" "$destino"
}

descargar_anotaciones() {
  local destino="$DESTINO/anotaciones_but"
  if [ "$(cat "$destino/VERSION_BUT.txt" 2>/dev/null)" = "$BUT_COMMIT" ]; then
    echo "Ya están: anotaciones de BUT"
    return 0
  fi
  echo "Descargando las anotaciones de BUT"
  local temporal
  temporal="$(mktemp -d)"
  git clone --quiet --no-checkout "$BUT_REPO" "$temporal/but"
  git -C "$temporal/but" checkout --quiet "$BUT_COMMIT"
  if [ "$(git -C "$temporal/but" rev-parse HEAD)" != "$BUT_COMMIT" ]; then
    rm -rf "$temporal"
    echo "Las anotaciones de BUT no están en el commit $BUT_COMMIT" >&2
    return 1
  fi
  rm -rf "$temporal/but/.git" "$destino"
  mv "$temporal/but" "$destino"
  echo "$BUT_COMMIT" > "$destino/VERSION_BUT.txt"
  rm -rf "$temporal"
}

mkdir -p "$DESTINO/audios"
for reunion in IB4002 IB4010 EN2002a EN2002c ES2004a IS1009a TS3003a; do
  descargar_audio "$reunion"
done
descargar_anotaciones
echo "Datos listos en $DESTINO"
