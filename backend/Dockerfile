# API de athenis-voces: analiza la voz de las reuniones y sirve los resultados en el puerto 8000.
# Funciona en CPU; con docker-compose.gpu.yml usa la GPU NVIDIA (torch trae su CUDA).
FROM python:3.12.15-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /bin/

# ffmpeg convierte el audio subido y ffprobe mide su duración
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    CARPETA_TRABAJO=/trabajo \
    HF_HOME=/modelos

WORKDIR /app/backend

# Primero solo las dependencias, para que Docker las reutilice si cambia el código
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --group audio --no-install-project

COPY src/ ./src/
COPY ejemplos/ ./ejemplos/

# El audio subido y los modelos descargados van a volúmenes, nunca a la imagen
RUN useradd --create-home --uid 1000 athenis \
    && mkdir -p /trabajo /modelos \
    && chown athenis /trabajo /modelos
USER athenis

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/salud', timeout=4)"]

# Un solo proceso: el registro de análisis vive en memoria
CMD ["uvicorn", "api.app:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
