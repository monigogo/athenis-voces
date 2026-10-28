# Tasks: Producto (servidor HTTP de la API interna)

**Input**: Documentos de diseño en `specs/003-producto/`

**Referencias**: [plan.md](plan.md) · [spec.md](spec.md) · [research.md](research.md) · [data-model.md](data-model.md) · [contracts/api-http.md](contracts/api-http.md) · [quickstart.md](quickstart.md)

**Constitución punto 2 — TDD obligatorio**: cada tarea de implementación va precedida de su tarea de test. El test se escribe primero y debe fallar antes de tocar el código. Los documentos `.md` no llevan prueba.

**Estado al crear este fichero (2026-10-27)**: nada implementado. La implementación espera el visto bueno del equipo a este fichero.

**Alcance acordado (27 oct)**: en este trabajo solo se hace el backend: T001–T025, T032, T034, T036, T038, T040–T043, T049–T052 y la parte de backend de T046–T048. Las tareas de la web (T026–T031, T033, T035, T037, T039) son de la persona C. T044–T045 quedan fuera. Orden: fases 1, 2 y 3; después ejemplos y retención; después modo manual, demo pública y modelos cargados una vez; T025 al final.

## Formato: `[ID] [P?] [Story?] Descripción`

- **[P]**: se puede ejecutar en paralelo (ficheros distintos, sin dependencias incompletas)
- **[Story]**: historia de usuario de la spec a la que pertenece (US1–US6)

---

## Phase 1: Setup (Infraestructura compartida)

**Propósito**: dependencias, umbrales y paquete.

- [X] T001 Añadir `fastapi`, `uvicorn` y `python-multipart` a `dependencies`, y `httpx` al grupo `dev`, en `backend/pyproject.toml`; ejecutar `uv lock`
- [X] T002 [P] Test en `backend/tests/test_config.py`: `subida_max_bytes` (200 MB), `subida_max_segundos` (3600) y `retencion_segundos` (86 400) con sus valores iniciales y rechazados si no son positivos
- [X] T003 Añadir esos tres umbrales a `backend/src/config.py`, marcados [VALIDAR] (aclaraciones 1 y 2)
- [X] T004 [P] Crear `backend/src/api/__init__.py` y `backend/ejemplos/` (al principio, con los tres `Resultado` sintéticos de `backend/tests/ejemplos/`; ahora, con IB4002 e IB4010)

---

## Phase 2: Foundation (Prerrequisitos bloqueantes)

**Propósito**: aplicación, registro y cola, que usan todas las rutas.

- [X] T005 `backend/tests/conftest.py`: fixtures con un `Pasos` falso (turnos de dos voces presentes, sin modelos), un WAV mono 16 kHz generado en `tmp_path`, un ejecutor síncrono y un `TestClient` de `crear_app(...)` con `CARPETA_TRABAJO` en `tmp_path`
- [X] T006 [P] Test en `backend/tests/test_api_registro.py`: crear, consultar y actualizar análisis; 404 para un id desconocido; guardar el último `EstadoAnalisis` notificado
- [X] T007 [P] Test en `backend/tests/test_api_ajustes.py`: `CARPETA_TRABAJO`, `EJEMPLOS_DIR` y `DEMO_PUBLICA` desde el entorno, con sus valores por defecto; la carpeta de trabajo por defecto no está dentro del repositorio
- [X] T008 `backend/src/api/registro.py` y `backend/src/api/ajustes.py`
- [X] T009 `backend/src/api/cola.py`: ejecutor de un solo trabajador que lanza la fase 1 (`preparar_para_confirmar`) y la fase 2 (`analizar_confirmado`) de `pipeline.py` sin modificarlo
- [X] T010 `backend/src/api/app.py`: `crear_app(pasos, ajustes, ejecutor, reloj)` y `app` para uvicorn

**Checkpoint**: se puede escribir la prueba de cualquier ruta contra la aplicación con pasos falsos.

---

## Phase 3: Historias 1, 2 y 3 — Camino mínimo en el backend (P1) 🎯 MVP

**Objetivo**: salud, subir un audio, estado, hablantes para confirmar, fragmento, confirmación y resultado.

**Prueba independiente**: con pasos falsos, un audio subido llega a «terminado» y su resultado cumple el contrato; los rechazos de la subida no crean ningún análisis.

### Tests — camino mínimo (escribir primero; deben fallar)

- [X] T011 [P] [US1] `backend/tests/test_api_salud.py`: `GET /salud` responde 200 `{"estado": "ok"}`
- [X] T012 [P] [US1] `backend/tests/test_api_subida.py`: un WAV válido da 201 `EstadoAnalisis` en `en_cola`; un `.mp3` que es texto da 415; más de 200 MB da 413, también si `Content-Length` miente; sin `Content-Length` da 411; más de 60 min da 422 (`ffprobe` falso); sin audio ni ejemplo da 400; tras un rechazo no queda ningún fichero ni análisis; el nombre en disco es `<id>.subida` y el nombre original no sale en ninguna respuesta (FR-001, FR-002, SC-005)
- [X] T013 [P] [US1] Mismo fichero: detección del tipo real por los bytes de WAV, MP3 (ID3 y trama), OGG, FLAC y M4A
- [X] T014 [P] [US1] `backend/tests/test_api_recorrido.py`: `GET /analisis/{id}` pasa por los estados de RF-04 hasta `esperando_confirmacion`; un paso que falla da `error` con su motivo; 404 si no existe (FR-003)
- [X] T015 [P] [US2] Mismo fichero: `GET /hablantes` devuelve solo las voces presentes; 409 antes de tiempo; `POST /confirmacion` da 202 y lleva a `terminado`; 422 si no confirma justo las voces presentes o el cuerpo no cumple el contrato; 409 si se confirma dos veces; el origen de cada etiqueta llega al resultado (FR-005, FR-006)
- [X] T016 [P] [US3] Mismo fichero: `GET /resultado` devuelve el `Resultado` con el `id_analisis` del análisis; 409 si no está terminado (FR-007)
- [X] T017 [P] [US3] `backend/tests/test_api_fragmento.py`: devuelve un WAV mono 16 kHz con la duración pedida; 422 si dura más de 15 s, si `fin <= inicio`, si `inicio < 0` o si `fin` pasa de la duración; 409 sin WAV (FR-008, SC-007)

### Implementación — camino mínimo

- [X] T018 [US1] `GET /salud` en `backend/src/api/app.py`
- [X] T019 [US1] `backend/src/api/subida.py`: límite por `Content-Length` y por trozos, bytes mágicos y duración con `ffprobe` sin shell, con tiempo máximo y la ruta como `file:` (RNF-10)
- [X] T020 [US1] `POST /analisis` (audio) y `GET /analisis/{id}` en `backend/src/api/app.py`
- [X] T021 [US2] `GET /analisis/{id}/hablantes` y `POST /analisis/{id}/confirmacion`; `ConfirmacionInvalida` → 422
- [X] T022 [US3] `GET /analisis/{id}/resultado`
- [X] T023 [US3] `backend/src/api/fragmento.py` y `GET /analisis/{id}/fragmento`
- [X] T024 [US1] `backend/src/api/pasos_reales.py`: `Pasos` con `preparar`, `diarizar`, `proponer_voz`, `elegir_fragmentos` y `analizar`; `app` lo usa por defecto
- [X] T025 [US1] Test lento en `backend/tests/test_api_real.py` (`@pytest.mark.slow`): recorrido completo con los modelos reales sobre un audio de `datos/` (fuera del repositorio). *Escrito; sin el grupo `audio` ni los datos de AMI se salta, así que falta ejecutarlo en la máquina con GPU. La parte de `ffprobe` real sí pasa.*

**Checkpoint**: el camino mínimo funciona con curl (quickstart, apartado 3).

---

## Phase 4: Camino mínimo en la web (P1) 🎯 MVP — persona C

**Objetivo**: la web usa el servidor en vez de simular.

**Prueba independiente**: con `fetch` simulado, la web recorre subir → estado → hablantes → confirmación → resultado llamando a las rutas de 9.3.

### Tests — web (escribir primero; deben fallar)

- [ ] T026 [P] [US1] `frontend/src/test/api.test.ts`: `subirAudio` envía `multipart` a `/api/analisis` y consulta `/api/analisis/{id}` hasta `esperando_confirmacion` o `error`; muestra el motivo del error del servidor
- [ ] T027 [P] [US2] Mismo fichero: `getHablantes` y `enviarConfirmacion` llaman a sus rutas; `getResultado` devuelve lo que da el servidor, sin datos inventados
- [ ] T028 [P] [US3] Mismo fichero: la URL de un fragmento recorta el tramo a 15 s y empieza como mucho 1 s antes del evento (RF-18)

### Implementación — web

- [ ] T029 [US1] `frontend/src/services/api.ts`: llamadas reales a las rutas de 9.3; se quitan la simulación, los hablantes inventados y el resultado de ejemplo con etiquetas cambiadas
- [ ] T030 [US3] `frontend/src/services/audioPlayer.ts`: reproduce el WAV de `GET /fragmento` en vez de decodificar el fichero local
- [ ] T031 [US1] `frontend/src/App.tsx`: sin backend, la cabecera lo dice y la subida se desactiva con su motivo

**Checkpoint**: recorrido completo desde la web (quickstart, apartado 5).

---

## Phase 5: Historia 4 — Ejemplos precalculados (P2)

**Objetivo**: ver un ejemplo en 2 s o menos, sin confirmación.

### Tests

- [X] T032 [P] [US4] `backend/tests/test_api_ejemplos.py`: `GET /ejemplos` lista los `Resultado` de `EJEMPLOS_DIR`; `POST /analisis` con `ejemplo` crea un análisis `terminado` cuyo resultado es el del ejemplo; 404 con un ejemplo desconocido; 400 si llegan audio y ejemplo a la vez; no se lee nada de `tests/` (FR-009)
- [ ] T033 [P] [US4] `frontend/src/test/api.test.ts`: los ejemplos vienen de `/api/ejemplos`

### Implementación

- [X] T034 [US4] `GET /ejemplos` y `POST /analisis` con `ejemplo` en `backend/src/api/app.py`
- [ ] T035 [US4] `frontend/src/services/api.ts` y `frontend/src/views/AnalizarView.tsx`: ejemplos desde el servidor; el texto de cada ejemplo dice que es un resultado del sistema sobre una reunión AMI, con etiquetas del modelo sin confirmación humana y sin audio

---

## Phase 6: Modo manual (P2)

**Objetivo**: con el modo manual, el clasificador no se ejecuta (RF-08).

### Tests

- [X] T036 [P] [US2] `backend/tests/test_api_modo_manual.py`: con `modo_manual=true`, un `proponer_voz` que falla si se le llama no se llama y `hablantes` llega sin propuesta; sin el campo, sí se llama
- [X] T037 [P] [US2] `frontend/src/test/api.test.ts`: `subirAudio` envía `modo_manual`

### Implementación

- [X] T038 [US2] Campo `modo_manual` en `POST /analisis`, que llega a `preparar_para_confirmar`
- [X] T039 [US2] `frontend/src/views/AnalizarView.tsx` y `ConfirmarVocesView.tsx`: el modo manual se elige antes de subir y la pantalla de confirmar deja de cambiarlo

---

## Phase 7: Historia 6 — Retención de 24 h (P2) [VALIDAR]

**Objetivo**: pasado el plazo no queda audio en disco (RF-23).

### Tests

- [X] T040 [P] [US6] `backend/tests/test_api_retencion.py`: con un reloj falso a 24 h y 1 s, `borrar_caducados` borra `<id>.subida` y `<id>.wav` y conserva el `Resultado`; un análisis sin terminar pasa a `error` con el motivo de la retención; `fragmento` y `hablantes` dan 410; también borra ficheros huérfanos con más de 24 h; nada más joven se toca (FR-011, SC-006)

### Implementación

- [X] T041 [US6] `backend/src/api/retencion.py`: `borrar_caducados(ahora)` y un hilo que la ejecuta cada 10 min mientras el servidor está en marcha

---

## Phase 8: Demo pública sin subidas (P2) [VALIDAR]

### Tests

- [X] T042 [P] [US4] `backend/tests/test_api_subida.py`: con `DEMO_PUBLICA=1`, subir un audio da 403 y elegir un ejemplo sigue funcionando (FR-016)

### Implementación

- [X] T043 [US4] Comprobación de `DEMO_PUBLICA` en `POST /analisis`

---

## Phase 8b: Seguridad de la subida y modelos cargados una vez

- [X] T049 [P] [US1] Test en `backend/tests/test_api_subida.py`: tras subir un audio de más de 1 MB no queda ninguna copia en el directorio temporal del sistema, solo `<id>.subida` en `CARPETA_TRABAJO` (RNF-10, RD-04)
- [X] T050 [US1] `backend/src/api/subida.py`: leer el `multipart` por trozos y escribir el audio directamente en `CARPETA_TRABAJO`, sin la copia temporal que deja Starlette al leer el formulario
- [X] T051 [P] Test en `backend/tests/test_modelos_una_vez.py`: dos llamadas a `diarizar` y dos a `proponer_voz` cargan cada modelo una sola vez, en la primera llamada; si la carga falla, la siguiente llamada lo vuelve a intentar
- [X] T052 `backend/src/audio/diarizacion.py` y `backend/src/voz/clasificador.py`: guardar el modelo cargado y reutilizarlo en las llamadas siguientes

---

## Phase 9: Tipos de la web desde OpenAPI (FR-015) — fuera de este trabajo

- [ ] T044 [P] Test en `frontend/src/test/contrato.test.ts`: los tipos de `types/contrato.ts` salen de `types/api.ts` (generado), no se escriben a mano
- [ ] T045 Añadir `openapi-typescript` como dependencia de desarrollo y el script `pnpm tipos`, que genera `frontend/src/types/api.ts` desde `/openapi.json`; `types/contrato.ts` reexporta desde ahí

---

## Phase 10: Polish

- [ ] T046 [P] `README.md`: cómo arrancar el servidor y la web (quickstart, apartados 2 y 5). *Backend hecho (27 oct); la web queda para la persona C.*
- [ ] T047 Pasar `uv run ruff check src/ tests/ scripts/`, `uv run pytest tests/ -m "not slow"`, `scripts/revisar_seguridad.sh`, `pnpm lint`, `pnpm test` y `pnpm build`. *Backend (27 oct): ruff limpio; pytest con 542 en verde y 4 fallos de `test_descargar_datos.py` que ya existían antes de este trabajo; pip-audit y bandit limpios. Pendiente: gitleaks (no instalado en la máquina) y la parte web.*
- [ ] T048 Recorrer [quickstart.md](quickstart.md) entero con el servidor real. *Hecho con uvicorn y ffprobe reales hasta la separación de voces (salud, subida, rechazo 415, estado con su motivo de error). Falta el recorrido con los modelos, en la máquina con GPU.*

---

## Dependencias y orden

- Phase 1 → Phase 2 → Phase 3 → Phase 4: el camino mínimo, de punta a punta.
- Phases 5 a 8 dependen de la 3 y son independientes entre sí; su parte web, de la 4.
- Phase 9 depende de la 3 (necesita `/openapi.json`).
- Dentro de cada fase, los tests van antes que su implementación (constitución 2).

## Fuera de este fichero

- Fallos de las pantallas señalados en la revisión del 27 oct: confirmación rellenada de antemano, reproductor, colores de los índices, fórmulas, etc.
- Página «Cómo funciona» (US5, RF-22).
- Reintentar sin volver a subir (FR-004): 9.3 no tiene ruta para eso.
