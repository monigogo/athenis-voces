"""Pruebas de los dos entornos de desarrollo de VS Code: con GPU (NVIDIA) y solo con CPU.

Cada uno está en su carpeta de .devcontainer/: al abrir el proyecto, VS Code pregunta cuál usar.
"""

import json
from pathlib import Path

import pytest

DEVCONTAINER = Path(__file__).resolve().parents[2] / ".devcontainer"
ENTORNOS = ("cpu", "gpu")


def configuracion(entorno: str) -> dict:
    return json.loads((DEVCONTAINER / entorno / "devcontainer.json").read_text(encoding="utf-8"))


def test_solo_hay_los_dos_entornos():
    """Sin un devcontainer.json suelto en la raíz, VS Code siempre pregunta cuál usar."""
    assert not (DEVCONTAINER / "devcontainer.json").exists()
    for entorno in ENTORNOS:
        assert (DEVCONTAINER / entorno / "devcontainer.json").is_file()


def test_los_dos_usan_la_misma_imagen_y_las_mismas_herramientas():
    cpu, gpu = configuracion("cpu"), configuracion("gpu")
    assert cpu["build"] == gpu["build"] == {"dockerfile": "../Dockerfile"}
    assert cpu["features"] == gpu["features"]
    assert cpu["postCreateCommand"] == gpu["postCreateCommand"]


def test_la_imagen_quita_el_repositorio_de_yarn():
    """La imagen base trae el repositorio de Yarn con la clave GPG caducada: apt-get update
    falla y las features (docker-outside-of-docker) no se instalan."""
    dockerfile = (DEVCONTAINER / "Dockerfile").read_text(encoding="utf-8")
    assert "FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm" in dockerfile
    assert "rm -f /etc/apt/sources.list.d/yarn.list" in dockerfile


@pytest.mark.parametrize("entorno", ENTORNOS)
def test_cada_entorno_trae_lo_que_necesita_el_proyecto(entorno):
    c = configuracion(entorno)
    assert "ffmpeg" in c["postCreateCommand"]  # preparar.py y ffprobe
    assert "corepack enable pnpm" in c["postCreateCommand"]  # la web, solo con pnpm (regla 5)
    assert any("/uv:" in nombre for nombre in c["features"])
    assert c["features"]["ghcr.io/devcontainers/features/node:1"]["version"] == "22"  # como el CI


@pytest.mark.parametrize("entorno", ENTORNOS)
def test_abre_los_puertos_de_la_api_y_de_la_web(entorno):
    # 8000 y 5173 en desarrollo; 8080, la web desplegada con docker compose
    assert configuracion(entorno)["forwardPorts"] == [8000, 5173, 8080]


@pytest.mark.parametrize("entorno", ENTORNOS)
def test_usa_el_docker_del_ordenador(entorno):
    """docker compose se lanza desde dentro, pero construye y corre en el Docker del ordenador."""
    assert (
        "ghcr.io/devcontainers/features/docker-outside-of-docker:1"
        in (configuracion(entorno)["features"])
    )


@pytest.mark.parametrize("entorno", ENTORNOS)
def test_comparten_la_cache_de_descargas(entorno):
    """PyTorch, TensorFlow y CUDA ocupan varios GB: no se bajan otra vez al cambiar de entorno."""
    assert (
        "source=athenis-voces-uv-cache,target=/home/vscode/.cache/uv,type=volume"
        in (configuracion(entorno)["mounts"])
    )
    # El volumen se crea con dueño root; uv trabaja como vscode y, si no, no podría escribir
    assert (
        "sudo chown -R vscode:vscode /home/vscode/.cache/uv"
        in (configuracion(entorno)["postCreateCommand"])
    )


def test_el_de_gpu_usa_la_gpu_y_lo_exige():
    gpu = configuracion("gpu")
    assert "--gpus=all" in gpu["runArgs"]
    # Pedir «cuda» sin GPU da un error claro, en vez de medir en la CPU sin avisar (RNF-01)
    assert gpu["containerEnv"]["DISPOSITIVO"] == "cuda"


def test_el_de_cpu_no_pide_gpu():
    cpu = configuracion("cpu")
    assert "--gpus=all" not in cpu.get("runArgs", [])
    assert cpu["containerEnv"]["DISPOSITIVO"] == "cpu"
