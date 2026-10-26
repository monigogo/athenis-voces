# Tasks: Análisis y evaluación

**Input**: Documentos de diseño en `specs/002-analisis/`

**Referencias**: [plan.md](plan.md) · [spec.md](spec.md) · [research.md](research.md) · [data-model.md](data-model.md) · [contracts/modulos-analisis.md](contracts/modulos-analisis.md) · [quickstart.md](quickstart.md)

**Constitución punto 2 — TDD obligatorio**: cada tarea de implementación va precedida de su tarea de test. El test se escribe primero y debe fallar antes de tocar el módulo. Los documentos `.md` no llevan prueba.

**Estado al crear este fichero (2026-10-25)**: el análisis y casi toda la evaluación ya están hechos y probados (`[X]`). Quedan las tareas con `[ ]`.

## Formato: `[ID] [P?] [Story?] Descripción`

- **[P]**: se puede ejecutar en paralelo (ficheros distintos, sin dependencias incompletas)
- **[Story]**: historia de usuario a la que pertenece (US1–US6)

---

## Phase 1: Setup (Infraestructura compartida)

**Propósito**: paquetes, dependencias y configuración.

- [X] T001 Crear `backend/src/analisis/__init__.py` y `backend/src/evaluacion/__init__.py`
- [X] T002 Añadir `pyannote-metrics` al grupo `evaluacion` de `[dependency-groups]` en `backend/pyproject.toml`
- [X] T003 Poner todos los umbrales y pesos en `backend/src/config.py` con su prueba en `backend/tests/test_config.py` (FR-012)
- [ ] T004 [P] Añadir `pytest-cov` al grupo `dev` de `backend/pyproject.toml` y ejecutar `uv lock` (SC-007)

---

## Phase 2: Foundation (Prerequisitos bloqueantes)

**Propósito**: el contrato y los ejemplos con los que se prueba todo.

- [X] T005 Entradas y resultados del contrato en `backend/src/contrato.py`, sin campos nuevos (constitución 3)
- [X] T006 [P] Análisis falso con los tres ejemplos en `backend/src/analisis/falso.py`, con `backend/tests/test_falso_analisis.py`

**Checkpoint**: se puede escribir cualquier prueba del análisis contra un `EntradaAnalisis` inventado.

---

## Phase 3: Historia 1 — Presencia y participación (P1) 🎯 MVP

**Objetivo**: voces por grupo, primera intervención femenina y cuotas de tiempo y de turnos, sin las señales de escucha en los turnos.

**Prueba independiente**: 3 casos sintéticos calculados a mano; todas las cifras coinciden (SC-001).

### Tests — Historia 1 (escribir primero; deben fallar)

- [X] T007 [US1] `backend/tests/test_participacion.py`: voz femenina presente con 10 s o más (MD-01, RN-01), voces por grupo (MD-02), primera intervención (MD-03), cuotas (MD-04, MD-05), turnos de más de 30 s (MD-06)
- [X] T008 [US1] En el mismo fichero: «indeterminado» fuera del denominador y aparte (RN-03, RN-04); el solapamiento cuenta entero para cada persona (aclaración 1); las señales de escucha no cuentan como turno (D-14)

### Implementación — Historia 1

- [X] T009 [US1] `backend/src/analisis/participacion.py`: `turnos_que_cuentan`, `por_hablante`, `por_grupo` y `presencia` (FR-001, FR-010, FR-018)

**Checkpoint**: Historia 1 completa.

---

## Phase 4: Historia 2 — Quién abre y quién cierra (P1)

**Objetivo**: primer y último turno de más de 5 s.

**Prueba independiente**: los mismos 3 casos sintéticos, con abre y cierra calculados a mano.

### Tests — Historia 2

- [X] T010 [US2] `backend/tests/test_posicion.py`: se salta un primer turno de 5 s o menos (MD-07); el último turno de más de 5 s (MD-08); `None` si ninguno lo supera

### Implementación — Historia 2

- [X] T011 [US2] `backend/src/analisis/posicion.py`: `quien_abre` y `quien_cierra` (FR-002)

**Checkpoint**: Historia 2 completa.

---

## Phase 5: Historia 3 — Detectar y clasificar interrupciones (P1)

**Objetivo**: candidatos, los tres tipos y las métricas MD-14 a MD-17, solo con tiempos.

**Prueba independiente**: un caso sintético de cada tipo se clasifica bien (SC-002).

### Tests — Historia 3

- [X] T012 [US3] `backend/tests/test_interrupciones.py`: pisarse 0,3 s o menos no es candidato; «con éxito» (A calla en 2 s desde que B empieza, aclaración 3); «intento» (B habla 1 s o más); «señal de escucha» (menos de 1 s, no cuenta); inicio y fin en cada interrupción (RN-06)
- [X] T013 [US3] En el mismo fichero: recibidas y hechas por persona, tasa por 10 min de habla propia, recupera la palabra en 10 s o menos, apoyos por 10 min (MD-14 a MD-17, RN-08); persona sin tiempo propio da `None`

### Implementación — Historia 3

- [X] T014 [US3] `backend/src/analisis/interrupciones.py`: `detectar`, `por_hablante` y `por_grupo` (FR-003 a FR-006, FR-011)

**Checkpoint**: Historia 3 completa.

---

## Phase 6: Historia 4 — Ratio de representación y brecha de interrupción (P1)

**Objetivo**: RR y BI con su fórmula, y «no aplicable» cuando el denominador es 0.

**Prueba independiente**: valores calculados a mano y la prueba de la RN-13 (SC-003).

### Tests — Historia 4

- [X] T015 [US4] `backend/tests/test_indices.py`: RR y BI calculados a mano; sin voces femeninas, sin masculinas o sin tiempo da `None`, nunca 0 ni error (RN-13); cada índice lleva su fórmula (RN-06)

### Implementación — Historia 4

- [X] T016 [US4] `backend/src/analisis/indices.py`: `ratio_representacion`, `brecha_interrupcion` y `de_grupo` (FR-007, FR-009)
- [X] T017 [US4] `backend/src/analisis/analizar.py` con `backend/tests/test_analizar.py`: junta todo y cumple la firma `Pasos.analizar` (FR-014); `backend/tests/test_ejemplos.py` comprueba los tres ejemplos del contrato

**Checkpoint**: Historia 4 completa. **Las historias 1 a 4 forman el MVP de la feature.**

---

## Phase 7: Historia 5 — Índice de protagonismo (P3, Should)

**Objetivo**: IP de 0 a 100 y su análisis de sensibilidad. Es lo primero que se recorta si falta tiempo.

**Prueba independiente**: la fórmula con un caso sintético, y que un componente con máximo 0 vale 0 para todas.

### Tests — Historia 5

- [X] T018 [US5] `backend/tests/test_indices.py`: IP calculado a mano; sin turnos largos, L vale 0 para todas; los pesos salen de la configuración
- [ ] T019 [US5] `backend/tests/test_indices.py`: `sensibilidad_protagonismo` devuelve, para cada uno de los tres pesos variado ± 50 %, si cambia el orden de las personas (11.3); sin cambios en los pesos, no hay cambio de orden

### Implementación — Historia 5

- [X] T020 [US5] `backend/src/analisis/indices.py`: `protagonismo` (FR-008)
- [ ] T021 [US5] `backend/src/analisis/indices.py`: `sensibilidad_protagonismo(segundos, abre, cierra, turnos_largos, config) -> dict[str, bool]` (FR-008, escenario 3)

**Checkpoint**: Historia 5 completa cuando T019 pase.

---

## Phase 8: Historia 6 — Evaluar el sistema (P2)

**Objetivo**: un solo script regenera las tablas de 12.1 sin volver a procesar el audio.

**Prueba independiente**: ejecutar el script con salidas guardadas y obtener las tablas con n e IC 95 % (SC-008).

### Tests — Historia 6

- [X] T022 [US6] `backend/tests/test_evaluacion.py`: DER (M-01), error del % femenino (M-04), emparejamiento con ± 1 s, precisión, exhaustividad y F1 (M-05), línea base de cualquier solapamiento, kappa de Cohen (M-08) y bootstrap con semilla fija
- [X] T023 [US6] `backend/tests/test_evaluar.py`: lee RTTM, JSON y etiquetas; lo que falta no se evalúa y no cuenta en n; la confirmación ideal asigna el sexo de AMI por solapamiento (decisión 6 de research.md)
- [X] T024 [US6] `backend/tests/test_cronometrar.py`: `minutos_por_hora(duracion_audio, segundos_proceso)` da los minutos de proceso por hora de audio (M-09); duración 0 da `None`

### Implementación — Historia 6

- [X] T025 [US6] `backend/src/evaluacion/lectura.py`, `metricas.py` y `evaluar.py` (FR-015, FR-016, FR-017)
- [X] T026 [US6] `backend/src/evaluacion/cronometrar.py`: `minutos_por_hora` y una línea de M-09 en la tabla de `evaluar.py` cuando hay tiempos guardados (escenario 5)

**Checkpoint**: Historia 6 completa cuando T024 pase. Después, la ejecución real con los datos (Phase 9).

---

## Phase 9: Ejecución real y cierre

**Propósito**: medir con audios de verdad. Nada de esto ajusta reglas (constitución 9).

- [ ] T027 Esperar las anotaciones de A y C de `conversacion1`, `conversacion2` y `EN2002a` (hasta el minuto 5:00) en `evaluacion/etiquetas/`, y que acuerden la referencia (`<audio>_referencia.txt`), según `evaluacion/guia_anotacion.md` (M-05, M-08)
- [ ] T028 Comprobar la kappa (SC-006): si es menor de 0,6 [VALIDAR], se revisa la guía y se vuelve a anotar
- [X] T029 Cronometrar 3 audios completos en GPU y guardar los tiempos fuera del repositorio (M-09, SC-008)
- [X] T030 Ejecutar `evaluacion.evaluar` sobre la partición de prueba, una vez por versión (FR-016), y guardar la tabla
- [ ] T031 [P] Crear `informe_evaluacion.ipynb` que llama a `evaluar.py` y muestra las tablas de 12.1 con su n y su IC 95 % (RNF-07). Sin audios ni nombres reales (RD-04)
- [ ] T032 [P] Anotar en el anexo C de `docs/01-funcional.md` cada cambio de regla o de umbral con su motivo y su fecha (FR-013, RD-06)
- [ ] T033 Comprobar la cobertura del módulo de análisis: 80 % de líneas o más (SC-007); añadir las pruebas que falten con la prueba escrita primero

---

## Dependencias

```text
Phase 1 -> Phase 2 -> Historia 1 -> Historia 2 -> Historia 3 -> Historia 4
                                                       Historia 4 -> Historia 5 (P3)
                                      Historia 4 -> Historia 6 -> Phase 9
```

- Historia 3 usa los turnos que deja Historia 1 (`turnos_que_cuentan`).
- Historia 4 usa los recuentos de Historia 1 y las interrupciones de Historia 3.
- Historia 6 usa `analizar` (T017).
- Phase 9 necesita las anotaciones (T027) y los audios de la partición de prueba.

## Ejecución en paralelo

- T004 puede ir a la vez que T019 y T024 (ficheros distintos).
- T031 y T032 pueden ir a la vez una vez hecha T030.

## Estrategia

1. **MVP**: Historias 1 a 4. Ya hecho.
2. **Después**: Historia 6 (T024, T026) y la ejecución real (Phase 9), que es obligatoria para entregar.
3. **Solo si sobra tiempo**: Historia 5 (T019, T021), porque el IP es Should.
