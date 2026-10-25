# Guía de validación: Análisis y evaluación

Cómo verificar que la feature funciona de extremo a extremo.

**Prerrequisito**: los audios y referencias de evaluación descargados con
`scripts/descargar_datos.sh` (constitución, punto 7). No se suben al repositorio.

---

## 1. Instalar

```bash
cd backend
uv sync --group evaluacion
```

## 2. Pruebas del análisis (SC-001 a SC-003)

```bash
cd backend
uv run pytest tests/test_participacion.py tests/test_posicion.py tests/test_interrupciones.py \
    tests/test_indices.py tests/test_analizar.py -v
```

**Esperado**: todo en verde. Incluye los 3 casos sintéticos calculados a mano, un caso de cada tipo
de interrupción y la prueba de «no aplicable».

## 3. Pruebas de la evaluación

```bash
cd backend
uv run pytest tests/test_evaluacion.py tests/test_evaluar.py -v
```

## 4. Cobertura del módulo de análisis (SC-007)

```bash
cd backend
uv run pytest tests/ --cov=src/analisis --cov-report=term-missing
```

**Esperado**: 80 % de líneas o más. `pytest-cov` todavía no está en las dependencias: añadirlo es
una tarea de `tasks.md`.

## 5. Regenerar la tabla 12.1 (SC-008)

Con los `.rttm` y `.json` guardados en `salidas/` (fuera del repositorio):

```bash
cd backend
PYTHONPATH=src uv run --group evaluacion python -m evaluacion.evaluar --salidas ../salidas
```

**Esperado**: una tabla con M-01, M-04, M-05, M-08 y la ablación, cada una con su n y su IC 95 %.
Dos ejecuciones seguidas dan exactamente la misma tabla (semilla fija).

## 6. Medir el tiempo (M-09)

Procesar 3 audios completos en GPU y cronometrar. **Esperado**: menos de 15 min de proceso por hora
de audio (RNF-01).
