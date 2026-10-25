# Tasks: Audio y voz

**Input**: Documentos de diseño en `specs/001-audio-voz/`

**Referencias**: [plan.md](plan.md) · [spec.md](spec.md) · [data-model.md](data-model.md) · [contracts/pipeline-pasos.md](contracts/pipeline-pasos.md) · [quickstart.md](quickstart.md)

**Constitución punto 2 — TDD obligatorio**: cada tarea de implementación va precedida de su tarea de test. El test se escribe primero y debe fallar antes de tocar el módulo.

## Formato: `[ID] [P?] [Story?] Descripción`

- **[P]**: se puede ejecutar en paralelo (ficheros distintos, sin dependencias incompletas)
- **[Story]**: historia de usuario a la que pertenece (US1–US4)

---

## Phase 1: Setup (Infraestructura compartida)

**Propósito**: crear la estructura de carpetas e instalar las dependencias nuevas.

- [X] T001 Crear `backend/src/audio/__init__.py` y `backend/src/voz/__init__.py` (nuevos paquetes)
- [X] T002 Añadir `pyannote.audio` e `inaSpeechSegmenter` al grupo `audio` en `[dependency-groups]` de `backend/pyproject.toml` (no a las dependencias base ni al grupo `dev`); ejecutar `uv lock` y, para usar los modelos, `uv sync --group audio`

---

## Phase 2: Foundation (Prerequisitos bloqueantes)

**Propósito**: cambios en módulos compartidos que todas las historias necesitan.

~~T003~~ *(eliminado — no se añade ningún campo a Config; el filtro de solapamientos lo aplica la persona B)*
~~T004~~ *(eliminado — sin cambios en config.py ni en test_config.py)*

**Fase vacía**: no quedan tareas. La Phase 3 depende directamente de Phase 1.

---

## Phase 3: Historia 1 — Preparar el audio y separar las voces (P1) 🎯 MVP

**Objetivo**: dado un audio de entrada en cualquier formato admitido, el sistema produce un WAV mono de 16 kHz y devuelve los turnos de cada hablante y todos los solapamientos detectados por pyannote.

**Prueba independiente**: pasar `IB4002_fragmento_5min.mp3`; comprobar que el WAV resultante es mono 16 kHz con duración ± 0,1 s y que la diarización devuelve ≥ 2 hablantes con turnos y solapamientos en el formato del contrato.

### Tests — Historia 1 (escribir primero; deben fallar)

- [X] T005 [US1] Escribir `backend/tests/test_preparar.py` con los siguientes casos (deben fallar antes de implementar):
  - **Con ffmpeg real** (`@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg no disponible")`): generar un WAV sintético de 2 s con el módulo `wave` (o con ffmpeg: `ffmpeg -f lavfi -i sine=frequency=440:duration=2 sintético.wav`), llamar a `preparar()` y comprobar con `wave.open` que el resultado es mono (1 canal), 16 000 Hz y duración ± 0,1 s (SC-001, RF-03)
  - **Con mock de `subprocess.run`**: formato no admitido (p. ej. `.xyz`) → `subprocess.run` lanza `FileNotFoundError` o devuelve `returncode != 0` → `preparar()` lanza excepción con mensaje claro (FR-008)
  - **Con mock de `subprocess.run`**: `subprocess.run` lanza `subprocess.TimeoutExpired` → `preparar()` lanza excepción
  - **Con mock de `subprocess.run`**: ruta de destino en directorio inexistente → `preparar()` lanza excepción

- [X] T006 [US1] Escribir `backend/tests/test_diarizacion.py` con los siguientes casos (deben fallar antes de implementar); usar un mock de pyannote (el import de `pyannote.audio` va dentro de la función, no al inicio del archivo) para no descargar modelos ni necesitar HF_TOKEN:
  - WAV con ≥ 2 hablantes → devuelve `list[Turno]` y `list[Solapamiento]` válidos (RF-05)
  - Todos los solapamientos detectados se devuelven, aunque sean muy cortos (sin filtro de duración)
  - Con cero o un hablante, diarizar devuelve los turnos y solapamientos detectados, sin lanzar excepción
  - Hablantes numerados 1, 2, 3 por orden de primera aparición; la numeración es estable para el mismo audio
  - Tramos de duración cero descartados del resultado
  - Si el modelo no carga o falta HF_TOKEN → excepción con motivo claro, sin incluir el valor del token
  - diarizar no devuelve ni guarda embeddings ni huellas de voz (RD-04)
  - Hablantes numerados desde 1, sin nombres ni identidades (RN-10)

### Implementación — Historia 1

- [X] T007 [US1] Implementar `backend/src/audio/preparar.py`: función `preparar(audio: Path, destino: Path) -> float` que convierte a WAV mono `config.frecuencia_muestreo` Hz llamando a ffmpeg con `subprocess.run` (sin `shell=True`, con `timeout`); calcula la duración leyendo el WAV resultante con `wave.open` (`nframes / framerate`); lanza excepción ante error (firma: contracts/pipeline-pasos.md)
- [X] T008 [US1] Implementar `backend/src/audio/diarizacion.py`: función `diarizar(wav: Path) -> tuple[list[Turno], list[Solapamiento]]` con pyannote `speaker-diarization-community-1`; devuelve todos los solapamientos detectados sin filtrar por duración; numera hablantes desde 1 por orden de primera aparición; lee HF_TOKEN del entorno, nunca lo registra en logs ni excepciones (RD-04); funciona en CPU (FR-011); el error por pocas voces lo da el pipeline (D-17, voces_presentes_minimas), no diarizar (firma: contracts/pipeline-pasos.md)

**Checkpoint**: Historia 1 completa y testeable de forma independiente. Ejecutar `quickstart.md` secciones 3 y 4.

---

## Phase 4: Historia 2 — Proponer cómo suena cada voz (P1)

**Objetivo**: para cada hablante separado, el sistema propone una etiqueta (femenino, masculino o indeterminado) con una confianza entre 0 y 1.

**Prueba independiente**: pasar audio AMI EN2002a (sexo de referencia conocido); comprobar que cada hablante recibe propuesta con etiqueta y confianza ∈ [0, 1]; los de confianza en [0,35–0,65] tienen etiqueta `indeterminado`.

**Dependencia**: requiere que T007 y T008 estén completos (usa el WAV preparado y los turnos de diarización).

### Tests — Historia 2 (escribir primero; deben fallar)

- [X] T009 [US2] Escribir `backend/tests/test_clasificador.py` con los siguientes casos (deben fallar antes de implementar); usar un mock de `inaSpeechSegmenter` (el import va dentro de la función, no al inicio del archivo) para no descargar modelos ni necesitar torch:
  - hablante con audio claro → propuesta con etiqueta y `confianza ∈ [0, 1]` (RF-06)
  - confianza en zona dudosa [0,35; 0,65] → etiqueta `indeterminado` (FR-004, RF-06)
  - confianza < 0,35 → etiqueta `masculino` o `femenino` según el modelo
  - confianza > 0,65 → etiqueta `masculino` o `femenino` según el modelo
  - el dict devuelto contiene exactamente los hablantes presentes en los turnos recibidos
  - propuesta registra que el origen es el modelo (FR-005): el campo `origen` de `EtiquetaConfirmada` lo fija el pipeline, no el clasificador — verificar que `PropuestaVoz` no incluye `origen` (ya está en el contrato)

### Implementación — Historia 2

- [X] T010 [US2] Implementar `backend/src/voz/clasificador.py`: función `proponer_voz(wav: Path, turnos: list[Turno]) -> dict[int, PropuestaVoz]` con `inaSpeechSegmenter.Segmenter` (import dentro de la función); aplica zona dudosa desde `config.zona_dudosa_min` / `config.zona_dudosa_max`; ejecuta el modelo una sola vez sobre el WAV completo y asigna los segmentos female/male a cada hablante por tiempo, sin contar los tramos compartidos con otros hablantes (firma: contracts/pipeline-pasos.md)

**Checkpoint**: Historia 2 completa. Ejecutar `quickstart.md` sección 5.

---

## Phase 5: Historia 3 — Dar fragmentos para confirmar cada voz (P1)

**Objetivo**: para cada hablante con ≥ 10 s de habla (presente si además tiene 3 tramos válidos, D-18), el sistema elige ≥ 3 fragmentos de 3–5 s, distribuidos uniformemente y sin solapamiento entre sí.

**Prueba independiente**: con audio separado, comprobar que cada hablante presente tiene ≥ 3 fragmentos de 3–5 s, no solapados entre sí, distribuidos uniformemente; hablantes con < 3 tramos válidos no aparecen en el dict.

**Dependencia**: requiere que T008 esté completo (usa turnos y solapamientos).

### Tests — Historia 3 (escribir primero; deben fallar)

- [X] T011 [US3] Escribir `backend/tests/test_fragmentos.py` con los siguientes casos (deben fallar antes de implementar):
  - hablante presente con ≥ 3 tramos válidos → ≥ 3 fragmentos de `[fragmento_min_segundos, fragmento_max_segundos]` (FR-006, SC-006)
  - fragmentos de un mismo hablante no se solapan entre sí (clarificación 2026-10-24)
  - fragmentos distribuidos uniformemente: el primero está en el primer tercio del audio del hablante, el último en el último tercio
  - fragmento no incluye tramos de solapamiento del hablante
  - hablante presente con < 3 tramos de ≥ 3 s → no aparece en el dict (Historia 3 escenario 2)
  - hablante con < `config.presencia_desde_segundos` (10 s) de habla → no aparece en el dict (RN-01)

### Implementación — Historia 3

- [X] T012 [US3] Implementar `backend/src/audio/fragmentos.py`: función `elegir_fragmentos(turnos: list[Turno], solapamientos: list[Solapamiento]) -> dict[int, list[Fragmento]]`; filtra tramos de solapamiento; aplica umbral de presencia; selecciona por distribución uniforme; garantiza no solapamiento entre fragmentos del mismo hablante (firma: contracts/pipeline-pasos.md)

**Checkpoint**: Historias 1, 2 y 3 completas. Ejecutar `quickstart.md` sección 6.

---

## Phase 6: Historia 4 — Modo manual, sin propuesta automática (P2)

**Objetivo**: cuando el modo manual está activo en un análisis, el clasificador de voz no se ejecuta y los hablantes llegan a confirmación sin propuesta.

**Prueba independiente**: con `modo_manual=True` en el pipeline, comprobar que `proponer_voz` no se llama ni una vez y que todos los hablantes tienen `propuesta=None`.

**Dependencia**: requiere que T007, T008, T011 y T012 estén completos (pipeline fase 1 completa).

### Tests — Historia 4 (escribir primero; deben fallar si el clasificador se llama)

- [X] T013 [US4] Añadir casos de modo manual a `backend/tests/test_pipeline.py`:
  - `modo_manual=True` → `proponer_voz` no se ejecuta (SC-005, FR-007); usar mock para verificar 0 llamadas
  - `modo_manual=True` → todos los hablantes en `HablantesParaConfirmar` tienen `propuesta=None` (RF-08)
  - `modo_manual=False` (por defecto) → `proponen_voz` sí se ejecuta

### Implementación — Historia 4

- [X] T014 [US4] Verificar en `backend/src/pipeline.py` que `modo_manual=False` es el valor por defecto de `preparar_para_confirmar` y que el bloque condicional existente es correcto con los módulos reales; ajustar si algún test de T013 falla por razones distintas a la lógica del clasificador

**Checkpoint**: Historia 4 completa. Ejecutar `quickstart.md` sección 7.

---

## Phase 7: Polish y validación transversal

**Propósito**: integración completa del pipeline con los módulos reales y validación end-to-end.

- [X] T015 [P] Añadir `backend/tests/test_pipeline_integracion.py`: prueba que `preparar_para_confirmar` con los cuatro módulos reales (no falsos) procesa `IB4002_fragmento_5min.mp3` y devuelve `HablantesParaConfirmar` válido; marcar con `@pytest.mark.slow` para excluirlo de la CI rápida; la CI ejecuta `uv run pytest tests/ -m "not slow"` (sin instalar el grupo `audio`); los tests slow se ejecutan localmente con `uv sync --group audio && uv run pytest tests/ -m slow`
- [ ] T016 Ejecutar la validación completa de `quickstart.md` sección 8 y confirmar que todos los tests pasan
- [X] T017 [P] Revisar que ningún log, excepción ni fichero temporal expone el contenido del audio o identifica a personas (constitución punto 7, RF-009)
- [X] T018 [P] Actualizar `backend/pyproject.toml` si alguna dependencia añadida en T002 necesita versión mínima explícita
- [X] T019 [US1] Escribir test y añadir `backend/scripts/analizar_audio.py`: recibe un audio y una carpeta de salida por argumento (CLI); rechaza rutas de salida dentro del repositorio (RD-04); ejecuta `preparar` y `diarizar`; escribe `<nombre>.rttm` con líneas `SPEAKER <nombre> 1 <inicio> <duración> <NA> <NA> <hablante> <NA> <NA>`, donde `<hablante>` es `hablante_1`, `hablante_2`, … (sin espacios, porque `evaluacion/evaluar.py` separa por espacios y lee el campo 8); depende de T008; test primero
- [ ] T020 [US1] Ampliar `backend/scripts/analizar_audio.py` para ejecutar el pipeline completo y escribir `<nombre>.json` con el formato de `Resultado`; en este comando de evaluación las voces se confirman automáticamente con la propuesta del modelo; depende de T010, T012 y de la respuesta de Mónica sobre la confirmación automática

---

## Dependencias y orden de ejecución

### Dependencias entre fases

- **Setup (Phase 1)**: sin dependencias — puede empezar inmediatamente
- **Foundation (Phase 2)**: vacía — no bloquea nada
- **US1 — Historia 1 (Phase 3)**: depende de Phase 1 — bloquea US2 y US3
- **US2 — Historia 2 (Phase 4)**: depende de Phase 3 (necesita WAV preparado y turnos)
- **US3 — Historia 3 (Phase 5)**: depende de Phase 3 (necesita turnos y solapamientos); independiente de US2
- **US4 — Historia 4 (Phase 6)**: depende de Phase 3, 4 y 5
- **Polish (Phase 7)**: depende de todas las historias deseadas

### Dependencias entre historias de usuario

- **US1 (P1)**: puede empezar tras Setup (Phase 1) — sin dependencias de otras historias
- **US2 (P1)**: depende de US1 (pipeline usa WAV y turnos reales)
- **US3 (P1)**: depende de US1; independiente de US2 → US2 y US3 pueden ejecutarse en paralelo
- **US4 (P2)**: depende de US1, US2 y US3

### Dentro de cada historia

1. Escribir el test y verificar que falla (constitución punto 2)
2. Implementar el módulo hasta que el test pase
3. No avanzar a la siguiente historia hasta que el checkpoint esté verde

### Oportunidades de paralelismo

- T001 y T002 (Setup) pueden ir en paralelo
- T005 y T006 (tests US1) pueden escribirse en paralelo antes de implementar
- T009 (test US2) y T011 (test US3) pueden escribirse en paralelo una vez que US1 está lista
- T010 (impl US2) y T012 (impl US3) pueden implementarse en paralelo

---

## Ejemplo de ejecución en paralelo — Historia 1

```bash
# Paso 1: escribir ambos tests a la vez (distintos ficheros)
# Agente A: backend/tests/test_preparar.py
# Agente B: backend/tests/test_diarizacion.py

# Paso 2: verificar que fallan
uv run pytest tests/test_preparar.py tests/test_diarizacion.py -v
# esperado: todos FAILED

# Paso 3: implementar en orden (preparar primero, porque diarizar lo necesita)
# Agente A: backend/src/audio/preparar.py
# (cuando T007 pasa) Agente A: backend/src/audio/diarizacion.py

# Paso 4: checkpoint
uv run pytest tests/test_preparar.py tests/test_diarizacion.py -v
# esperado: todos PASSED
```

---

## Estrategia de implementación

### MVP (solo Historia 1)

1. Completar Phase 1 (Setup)
2. Completar Phase 3 (US1: preparar + diarizar)
3. **Parar y validar**: ejecutar `quickstart.md` secciones 3 y 4

### Entrega incremental

1. Setup → base lista
2. Historia 1 → checkpoint → el pipeline puede separar voces
3. Historias 2 y 3 en paralelo → checkpoint → pipeline completo en modo asistido
4. Historia 4 → modo manual disponible
5. Polish → integración y validación final

### Estrategia en equipo (3 personas)

Una vez completada la Historia 1:
- Persona A: Historia 2 (clasificador de voz)
- Persona B: Historia 3 (fragmentos)
- Persona C: Historia 4 puede empezar a escribir los tests (T013) mientras esperan

---

## Notas

- `[P]` = ficheros distintos, sin dependencias incompletas
- `[USn]` = historia de usuario para trazabilidad con la spec
- TDD estricto: ningún módulo se implementa sin su test rojo previo (constitución punto 2)
- Los audios de evaluación no entran en el repositorio; usar `scripts/descargar_datos.sh` (constitución punto 7)
- Los tests marcados `@pytest.mark.slow` (T015) se excluyen de la CI rápida con `-m "not slow"`
