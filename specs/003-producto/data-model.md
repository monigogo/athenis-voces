# Modelo de datos: Producto (servidor HTTP)

**Rama**: `feat/vani/api-servidor` | **Fecha**: 2026-10-27

Los datos que salen y entran por la API son los del contrato:
[docs/contrato_de_datos.md](../../docs/contrato_de_datos.md) y `backend/src/contrato.py`, que no se
modifican (constitución 3). Aquí solo se describe el registro interno del servidor, que nunca sale
por la API tal cual.

---

## Análisis (registro interno, `api/registro.py`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_analisis` | texto | `uuid4` en hexadecimal, generado por el sistema |
| `estado` | `EstadoAnalisis` | El último estado que notificó el pipeline (contrato) |
| `creado_en` | fecha y hora UTC | Momento de la subida; de ahí cuenta la retención |
| `modo_manual` | sí/no | RF-08: si es sí, el clasificador no se ejecuta |
| `audio` | ruta o nada | `<CARPETA_TRABAJO>/<id>.subida`; nada después de la retención |
| `wav` | ruta o nada | `<CARPETA_TRABAJO>/<id>.wav`, el WAV mono 16 kHz de `preparar` |
| `preparado` | `Preparado` o nada | Lo que deja la fase 1 de `pipeline.py` para la fase 2 |
| `resultado` | `Resultado` o nada | Lo que deja la fase 2; es lo único que queda tras la retención |
| `es_ejemplo` | sí/no | Creado desde un ejemplo precalculado: sin audio ni confirmación |

El nombre original del fichero subido no se guarda en ningún campo (RNF-10, RD-04).

## Transiciones de estado

Son las de RF-04. El servidor solo añade el caso de la retención.

```text
POST /analisis (audio) ──► en_cola ──► procesando (0, 25, 50, 75 %) ──► esperando_confirmacion
                                            │                                   │
                                            └──► error (motivo)                 │ POST /confirmacion
                                                                                ▼
                                                     error (motivo) ◄── procesando (90 %) ──► terminado

POST /analisis (ejemplo) ──► terminado

retención cumplida, sin terminar ──► error («Se cumplió el plazo de retención»)
```

## Reglas de validación

| Regla | Dónde | Respuesta si no se cumple |
|-------|-------|---------------------------|
| Tamaño ≤ 200 MB [VALIDAR] | `Content-Length` y copia por trozos | 413 (411 sin `Content-Length`) |
| Tipo real WAV, MP3, OGG, FLAC o M4A | bytes mágicos | 415 |
| Duración ≤ 60 min [VALIDAR] | `ffprobe` | 422 |
| Demo pública sin subidas [VALIDAR] | `DEMO_PUBLICA` | 403 |
| Confirmación de justo las voces presentes | `pipeline.ConfirmacionInvalida` | 422 |
| Rutas que piden un estado concreto | registro | 409 |
| Fragmento: `0 ≤ inicio < fin ≤ duración` y como mucho 15 s | `api/fragmento.py` | 422 |
| Análisis inexistente | registro | 404 |
| Audio ya borrado por la retención | registro | 410 |

## Umbrales nuevos en `config.py`

Van con el resto de umbrales (un solo sitio) y se prueban en `tests/test_config.py`:

| Campo | Valor | Origen |
|-------|-------|--------|
| `subida_max_bytes` | 200 × 1024 × 1024 | Aclaración 1 [VALIDAR] |
| `subida_max_segundos` | 3600 | Aclaración 1 [VALIDAR] |
| `retencion_segundos` | 86 400 (24 h) | Aclaración 2, D-08 [VALIDAR] |

`escucha_max_segundos` (15 s) ya existe y limita los fragmentos.
