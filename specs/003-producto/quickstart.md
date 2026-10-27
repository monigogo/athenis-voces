# Guía de validación: Producto (servidor HTTP)

Cómo comprobar que la API funciona de punta a punta.

**Prerrequisitos**: ffmpeg instalado (`ffmpeg -version` y `ffprobe -version`). Para el análisis
real, el grupo `audio` y `HF_TOKEN` en el entorno (ver el README). Los audios de prueba nunca entran
en el repositorio (constitución 7).

---

## 1. Pruebas rápidas de la API

```bash
cd backend
uv run pytest tests/test_api_*.py -m "not slow" -v
```

**Esperado**: todo en verde, sin modelos ni GPU (usan un `Pasos` falso). Cubre las rutas de 9.3,
las reglas de la subida (SC-005), el límite de 15 s (SC-007), el modo manual y la retención
(SC-006).

## 2. Arrancar el servidor

```bash
cd backend
uv sync --group audio
uv run --env-file ../.env uvicorn api.app:app --app-dir src --port 8000
```

`--env-file` carga `HF_TOKEN`, `DISPOSITIVO` y el resto de variables de `.env` (ver `.env.example`).

El servidor se arranca con **un solo proceso**, sin `--workers`: el registro de análisis vive en la
memoria de ese proceso y la cola usa la única GPU. Con varios procesos, una petición podría llegar a
uno que no conoce el análisis.

`http://localhost:8000/docs` muestra las rutas; `http://localhost:8000/salud` responde
`{"estado": "ok"}`.

## 3. Recorrido mínimo con curl

```bash
curl -F "audio=@/ruta/fuera/del/repo/reunion.wav" http://localhost:8000/analisis
curl http://localhost:8000/analisis/<id>            # repetir hasta esperando_confirmacion
curl http://localhost:8000/analisis/<id>/hablantes
curl -o muestra.wav "http://localhost:8000/analisis/<id>/fragmento?inicio=2&fin=6"
curl -H "Content-Type: application/json" -d @confirmacion.json \
     http://localhost:8000/analisis/<id>/confirmacion
curl http://localhost:8000/analisis/<id>/resultado
```

**Esperado**: el resultado cumple el contrato y tiene el `id_analisis` del paso 1.

## 4. Rechazos (SC-005 y SC-007)

- Un `.mp3` que en realidad es texto → 415, y no aparece ningún análisis nuevo.
- Un fragmento de 16 s → 422.
- Con `DEMO_PUBLICA=1`, subir un audio → 403; elegir un ejemplo sigue funcionando.

## 5. Desde la web

```bash
cd frontend
pnpm dev
```

Con el servidor del apartado 2 en marcha: subir un audio, confirmar las voces escuchando sus
fragmentos y ver los resultados. La cabecera dice que el backend está conectado.
