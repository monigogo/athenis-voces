"""Pruebas del despliegue con Docker: la API y la web, sin datos ni claves dentro de las imágenes."""

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")  # viene con el grupo evaluacion, que instala la CI

RAIZ = Path(__file__).resolve().parents[2]
DOCKERFILES = {
    "backend": RAIZ / "backend" / "Dockerfile",
    "frontend": RAIZ / "frontend" / "Dockerfile",
}


def _ignorados(carpeta: str) -> set[str]:
    lineas = (RAIZ / carpeta / ".dockerignore").read_text(encoding="utf-8").splitlines()
    return {x.strip() for x in lineas if x.strip() and not x.startswith("#")}


@pytest.fixture(scope="module")
def compose():
    return yaml.safe_load((RAIZ / "docker-compose.yml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def backend_dockerfile():
    return DOCKERFILES["backend"].read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def nginx():
    return (RAIZ / "frontend" / "nginx.conf").read_text(encoding="utf-8")


@pytest.mark.parametrize("servicio", DOCKERFILES)
def test_imagenes_con_version_fija(servicio):  # 11.4: versiones fijadas
    texto = DOCKERFILES[servicio].read_text(encoding="utf-8")
    imagenes = re.findall(r"^FROM\s+(\S+)|--from=(\S+:\S+)", texto, flags=re.MULTILINE)
    nombres = [a or b for a, b in imagenes]
    assert nombres
    for imagen in nombres:
        assert re.search(r":\d+\.\d+\.\d+", imagen), imagen


@pytest.mark.parametrize("servicio", DOCKERFILES)
def test_no_corre_como_root(servicio):
    texto = DOCKERFILES[servicio].read_text(encoding="utf-8")
    assert re.search(r"^USER\s+(?!root)\S+", texto, flags=re.MULTILINE)


def test_backend_instala_con_el_lock_y_sin_herramientas_de_desarrollo(backend_dockerfile):
    assert "uv sync --frozen --no-dev --group audio" in backend_dockerfile


def test_backend_trae_ffmpeg(backend_dockerfile):  # lo usan la subida y la preparación del audio
    assert "ffmpeg" in backend_dockerfile


def test_backend_sirve_la_api_en_un_solo_proceso(backend_dockerfile):
    # El registro de análisis vive en memoria: con varios procesos se perdería
    cmd = next(x for x in backend_dockerfile.splitlines() if x.startswith("CMD"))
    assert "api.app:app" in cmd
    assert "--workers" not in cmd


def test_backend_comprueba_su_salud(backend_dockerfile):
    assert "HEALTHCHECK" in backend_dockerfile
    assert "/salud" in backend_dockerfile


@pytest.mark.parametrize("carpeta", ["backend", "frontend"])
@pytest.mark.parametrize("patron", [".env", ".env.*"])
def test_no_entran_claves(carpeta, patron):  # RD-04, constitución 7
    assert patron in _ignorados(carpeta)


@pytest.mark.parametrize("extension", ["mp3", "wav", "m4a", "ogg", "flac"])
def test_no_entran_audios(extension):  # RD-04
    assert f"**/*.{extension}" in _ignorados("backend")


def test_las_claves_llegan_del_entorno_y_no_de_la_imagen(compose):
    assert compose["services"]["backend"]["env_file"]


def test_la_api_no_se_publica_fuera(compose):  # solo la web la ve, a través de nginx
    assert "ports" not in compose["services"]["backend"]


def test_la_web_espera_a_que_la_api_este_sana(compose):
    espera = compose["services"]["frontend"]["depends_on"]["backend"]
    assert espera["condition"] == "service_healthy"


def test_funciona_sin_gpu(compose):  # RNF-20: la GPU se añade con docker-compose.gpu.yml
    assert "deploy" not in compose["services"]["backend"]
    gpu = yaml.safe_load((RAIZ / "docker-compose.gpu.yml").read_text(encoding="utf-8"))
    dispositivos = gpu["services"]["backend"]["deploy"]["resources"]["reservations"]["devices"]
    assert dispositivos[0]["driver"] == "nvidia"


def test_nginx_quita_el_prefijo_api_como_vite(nginx):  # misma ruta que en desarrollo
    assert re.search(r"location /api/\s*\{[^}]*proxy_pass http://backend:8000/;", nginx)


def test_nginx_admite_audios_de_200_mb(nginx):  # límite de subida de config.py
    assert re.search(r"client_max_body_size\s+20\dm;", nginx)


def test_nginx_devuelve_la_web_en_cualquier_ruta(nginx):
    assert "try_files $uri $uri/ /index.html;" in nginx
