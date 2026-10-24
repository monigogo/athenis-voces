# Plan de implementación: Audio y voz

**Rama**: `feat/vani/audio-voz` | **Fecha**: 2026-10-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification de `specs/001-audio-voz/spec.md`

---

## Resumen

Implementar los cuatro módulos de la fase 1 del pipeline: conversión de audio a WAV mono 16 kHz,
diarización con pyannote, propuesta de voz con inaSpeechSegmenter, y selección de fragmentos
distribuidos uniformemente. Los módulos cumplen las firmas del dataclass `Pasos` de `pipeline.py`
y no modifican el contrato de datos (`contrato.py`).

---

## Contexto técnico

**Lenguaje / versión**: Python 3.11 (`requires-python = ">=3.11"`)

**Dependencias principales**:
- `pydantic >= 2.14.1` (ya instalada)
- `pydub` + ffmpeg (conversión de audio, RF-03)
- `pyannote.audio` modelo `speaker-diarization-community-1` (diarización, RF-05)
- `inaSpeechSegmenter` (propuesta de voz, RF-06)

**Almacenamiento**: sistema de ficheros (WAV temporal durante el procesamiento; no persiste en el
repositorio, RD-04)

**Testing**: pytest (ya configurado en `pyproject.toml`)

**Plataforma**: Linux server (OVHcloud), CPU obligatorio (RNF-20); GPU para producción (Parte 5.2)

**Tipo de proyecto**: backend — módulos de biblioteca llamados por `pipeline.py`

**Objetivo de rendimiento**: fragmento de 5 min en CPU (desarrollo); 60 min en ≤ 15 min en GPU
(SC-007 [VALIDAR el 2026-10-25])

**Restricciones**: sin API externas (RF-010), sin GPU en desarrollo (RNF-20), sin audios en el
repositorio (RD-04)

**Escala**: reuniones de 30–90 min; hasta ~10 hablantes por reunión

---

## Verificación de la constitución

| Punto | Verificación | Estado |
|-------|-------------|--------|
| 1. Manda el funcional | Spec referencia `docs/01-funcional.md`; si hay conflicto manda el funcional | ✅ |
| 2. TDD obligatorio | Cada módulo empieza con su test fallando | GATE |
| 3. Contrato único | `contrato.py` no se modifica; solo se añade un campo a `config.py` | ✅ |
| 4. Todo gratuito | pydub (MIT), pyannote community (MIT), inaSpeechSegmenter (MIT) | ✅ |
| 5. uv solo en backend/ | `uv sync` en `backend/`; pnpm no aplica aquí | ✅ |
| 6. Solo analiza la voz | No se transcribe nada (inaSpeechSegmenter solo clasifica el sonido) | ✅ |
| 7. Sin audios en repo | Tests usan fixtures JSON; audios de evaluación fuera del repo | ✅ |
| 8. Tres opciones de confirmación | `EtiquetaVoz`: femenino / masculino / indeterminado | ✅ |
| 9. Reuniones de prueba solo miden | Partición de prueba no ajusta nada | ✅ |
| 10. Primero los Must | P1 primero: preparar, diarizar, proponer, fragmentos | ✅ |
| 11. Las 8 fases | Este fichero es la fase 3 (plan); no se empieza fase 4 sin él | ✅ |

**GATE TDD**: ninguna tarea de código empieza sin su prueba escrita y fallando (constitución 2).

---

## Estructura del proyecto

### Documentación de esta feature

```text
specs/001-audio-voz/
├── plan.md              ← este fichero
├── research.md          ← Phase 0 (generado)
├── data-model.md        ← Phase 1 (generado)
├── quickstart.md        ← Phase 1 (generado)
├── contracts/
│   └── pipeline-pasos.md ← Phase 1 (generado)
├── checklists/
│   └── requirements.md
└── tasks.md             ← Phase 2 (/speckit-tasks — aún no creado)
```

### Código fuente (a crear)

```text
backend/src/
├── audio/
│   ├── __init__.py
│   ├── preparar.py          # RF-03: convierte a WAV mono 16 kHz
│   ├── diarizacion.py       # RF-05: separa hablantes con pyannote
│   └── fragmentos.py        # RF-07: elige fragmentos distribuidos
├── voz/
│   ├── __init__.py
│   └── clasificador.py      # RF-06: propone voz con inaSpeechSegmenter
└── config.py                # añadir solapamiento_registro_desde_segundos

backend/tests/
├── test_preparar.py          # TDD: RF-03, SC-001
├── test_diarizacion.py       # TDD: RF-05, SC-002
├── test_fragmentos.py        # TDD: RF-07, SC-006
└── test_clasificador.py      # TDD: RF-06, SC-003, SC-004
```

---

## Artefactos de Phase 1

- [research.md](research.md) — decisiones técnicas sin NEEDS CLARIFICATION
- [data-model.md](data-model.md) — entidades y reglas de negocio
- [contracts/pipeline-pasos.md](contracts/pipeline-pasos.md) — firmas de los cuatro módulos
- [quickstart.md](quickstart.md) — escenarios de validación de extremo a extremo

---

## Complejidad

No hay violaciones de la constitución que justificar.
