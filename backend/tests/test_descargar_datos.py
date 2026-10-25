"""Pruebas de scripts/descargar_datos.sh (A09), con curl y git falsos: sin red ni audios reales."""

import hashlib
import os
import re
import subprocess
from pathlib import Path

import pytest

from evaluacion.evaluar import REUNIONES_PRUEBA

RAIZ = Path(__file__).resolve().parents[2]
SCRIPT = RAIZ / "scripts" / "descargar_datos.sh"
SUMAS = RAIZ / "scripts" / "ami.sha256"
REUNIONES_DESARROLLO = ("IB4002", "IB4010")  # funcional, 11.3
COMMIT_BUT = "2509d8933721023fab4def2618aabd5c28eb82e9"

CURL_FALSO = """#!/usr/bin/env bash
# Escribe en -o el texto «audio <URL>» y apunta la llamada
salida=""; url=""
while [ $# -gt 0 ]; do
  case "$1" in -o) salida="$2"; shift 2 ;; -*) shift ;; *) url="$1"; shift ;; esac
done
echo "$url" >> "$LLAMADAS"
printf 'audio %s' "$url" > "$salida"
"""

GIT_FALSO = """#!/usr/bin/env bash
# clone crea la carpeta; checkout deja los ficheros de BUT; rev-parse dice el commit pedido
echo "git $*" >> "$LLAMADAS"
case " $* " in
  *" clone "*) mkdir -p "${@: -1}/.git" ;;
  *" checkout "*) d="$2"; mkdir -p "$d/only_words/rttms/test"
                  echo x > "$d/README.md"; echo x > "$d/only_words/rttms/test/EN2002a.rttm"
                  echo "${@: -1}" > "$d/.git/HEAD_FALSO" ;;
  *" rev-parse "*) cat "$2/.git/HEAD_FALSO" ;;
esac
"""


def url_de(reunion):
    return (
        "https://groups.inf.ed.ac.uk/ami/AMICorpusMirror/amicorpus/"
        f"{reunion}/audio/{reunion}.Mix-Headset.wav"
    )


def suma_falsa(reunion):
    return hashlib.sha256(f"audio {url_de(reunion)}".encode()).hexdigest()


@pytest.fixture
def entorno(tmp_path):
    """PATH con curl y git falsos, y un fichero de sumas que casa con lo que escribe el curl."""
    falsos = tmp_path / "bin"
    falsos.mkdir()
    for nombre, texto in (("curl", CURL_FALSO), ("git", GIT_FALSO)):
        (falsos / nombre).write_text(texto, encoding="utf-8", newline="\n")
        (falsos / nombre).chmod(0o755)
    sumas = tmp_path / "sumas.sha256"
    reuniones = REUNIONES_DESARROLLO + REUNIONES_PRUEBA
    sumas.write_text(
        "".join(f"{suma_falsa(r)}  {r}.Mix-Headset.wav\n" for r in reuniones), encoding="utf-8"
    )
    llamadas = tmp_path / "llamadas.txt"
    llamadas.touch()
    env = {
        **os.environ,
        "PATH": f"{falsos}{os.pathsep}{os.environ['PATH']}",
        "SUMAS": str(sumas),
        "LLAMADAS": str(llamadas),
    }
    return tmp_path / "datos", env, sumas, llamadas


def ejecutar(destino, env):
    return subprocess.run(
        ["bash", str(SCRIPT), str(destino)], env=env, capture_output=True, text=True, check=False
    )


# --- Lo que fija el script ----------------------------------------------------------------


def test_la_sintaxis_es_correcta():
    subprocess.run(["bash", "-n", str(SCRIPT)], check=True)


def test_las_sumas_son_las_7_reuniones_del_funcional():  # 11.3
    nombres = re.findall(
        r"^[0-9a-f]{64}  (\w+)\.Mix-Headset\.wav$", SUMAS.read_text(), re.MULTILINE
    )
    assert sorted(nombres) == sorted(REUNIONES_DESARROLLO + REUNIONES_PRUEBA)


def test_las_anotaciones_de_but_van_a_un_commit_fijo():  # 11.4: versiones fijadas
    assert f'BUT_COMMIT="{COMMIT_BUT}"' in SCRIPT.read_text(encoding="utf-8")


# --- Lo que hace -----------------------------------------------------------------------------


def test_descarga_las_7_reuniones_y_las_anotaciones(entorno):
    destino, env, _, llamadas = entorno
    resultado = ejecutar(destino, env)
    assert resultado.returncode == 0, resultado.stderr

    for reunion in REUNIONES_DESARROLLO + REUNIONES_PRUEBA:
        assert (destino / "audios" / f"{reunion}.Mix-Headset.wav").is_file()
    but = destino / "anotaciones_but"
    assert (but / "only_words" / "rttms" / "test" / "EN2002a.rttm").is_file()
    assert (but / "VERSION_BUT.txt").read_text().strip() == COMMIT_BUT
    assert not (but / ".git").exists()  # solo los ficheros, sin el historial
    assert f"checkout --quiet {COMMIT_BUT}" in llamadas.read_text()


def test_no_vuelve_a_descargar_lo_que_ya_esta_bien(entorno):
    destino, env, _, llamadas = entorno
    ejecutar(destino, env)
    llamadas.write_text("")
    resultado = ejecutar(destino, env)
    assert resultado.returncode == 0, resultado.stderr
    assert llamadas.read_text() == ""


def test_si_un_audio_no_cuadra_para_y_no_lo_deja(entorno):  # datos no fiables
    destino, env, sumas, _ = entorno
    sumas.write_text(sumas.read_text().replace(suma_falsa("EN2002a"), "0" * 64))
    resultado = ejecutar(destino, env)
    assert resultado.returncode != 0
    assert "EN2002a" in resultado.stderr
    assert not (destino / "audios" / "EN2002a.Mix-Headset.wav").exists()


def test_un_audio_estropeado_se_vuelve_a_descargar(entorno):
    destino, env, _, llamadas = entorno
    ejecutar(destino, env)
    roto = destino / "audios" / "IS1009a.Mix-Headset.wav"
    roto.write_text("a medias")
    llamadas.write_text("")
    resultado = ejecutar(destino, env)
    assert resultado.returncode == 0, resultado.stderr
    assert llamadas.read_text().strip() == url_de("IS1009a")
