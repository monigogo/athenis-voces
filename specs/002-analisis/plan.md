# Plan de implementación: Análisis y evaluación

**Rama**: `feat/moni/analisis` | **Fecha**: 2026-10-25 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification de `specs/002-analisis/spec.md`

---

## Resumen

Calcular, a partir de los turnos y las etiquetas confirmadas, la presencia, la participación, quién
abre y quién cierra, las interrupciones por reglas de tiempo y los índices RR, BI e IP. Además,
medir cuánto acierta el sistema (M-01 a M-05, M-08 y M-09) con un único script que regenera las
tablas de la sección 12.1 sin volver a procesar el audio.

El análisis es una sola función, `analizar(EntradaAnalisis) -> Resultado`, que cumple la firma
`Pasos.analizar` de `pipeline.py`. Todo se calcula con tiempos: no se transcribe nada (constitución 6).
No modifica el contrato de datos.

---

## Contexto técnico

**Lenguaje / versión**: Python 3.11 (`requires-python = ">=3.11"`)

**Dependencias principales**:
- `pydantic >= 2.14.1` (contrato de datos)
- `pyannote.metrics` (solo el DER, M-01; grupo `evaluacion`)
- biblioteca estándar para el resto: el análisis no necesita más dependencias

**Almacenamiento**: ficheros. Entradas: `.rttm` y `.json` de las salidas, etiquetas de Audacity
(`.txt`). Nada de esto entra en el repositorio si contiene audio o nombres (RD-04).

**Testing**: pytest, con casos sintéticos calculados a mano (SC-001 a SC-003)

**Plataforma**: Linux, solo CPU para el análisis; la GPU solo se usa para cronometrar M-09

**Tipo de proyecto**: backend, módulos de biblioteca llamados por `pipeline.py` y un script de evaluación

**Objetivo de rendimiento**: el análisis tarda un tiempo despreciable frente a la separación de voces;
M-09 mide el proceso entero (menos de 15 min por hora de audio, RNF-01)

**Restricciones**: sin LLM y sin palabras (D-10); todos los umbrales en `config.py` (FR-012);
la partición de prueba solo mide (RD-05)

**Escala**: reuniones de 30 a 90 min, hasta unas 10 voces

---

## Verificación de la constitución

| Punto | Verificación | Estado |
|-------|-------------|--------|
| 1. Manda el funcional | La spec cita 6.7, 5.1 y 11 del funcional; si hay conflicto manda el funcional | ✅ |
| 2. TDD obligatorio | Cada módulo tiene su prueba escrita antes; las tareas nuevas empiezan por su prueba | GATE |
| 3. Contrato único | Solo se leen y rellenan `EntradaAnalisis` y `Resultado`; no se añade ningún campo | ✅ |
| 4. Todo gratuito | pyannote.metrics (MIT); lo demás es biblioteca estándar | ✅ |
| 5. uv solo en backend/ | Todo se instala y ejecuta con `uv` desde `backend/` | ✅ |
| 6. Solo analiza la voz | Solo tiempos y etiquetas; las anotaciones de interrupciones son tiempos y un tipo | ✅ |
| 7. Sin audios en repo | Se evalúa con RTTM, JSON y etiquetas; los audios se descargan aparte | ✅ |
| 8. Tres opciones de confirmación | Entran `femenino`, `masculino` e `indeterminado`; esta última nunca se reparte (RN-03) | ✅ |
| 9. Reuniones de prueba solo miden | `evaluar.py` no ajusta nada; las reglas se ajustan con IB4002 e IB4010 | ✅ |
| 10. Primero los Must | Primero P1 (historias 1 a 4); P2 (evaluación) después; P3 (IP) si sobra tiempo | ✅ |
| 11. Las 8 fases | Este fichero es la fase 3 (plan); no se empieza la fase 4 sin él | ✅ |

**GATE TDD**: ninguna tarea de código empieza sin su prueba escrita y fallando (constitución 2).

---

## Estructura del proyecto

### Documentación de esta feature

```text
specs/002-analisis/
├── plan.md                  ← este fichero
├── research.md              ← Phase 0
├── data-model.md            ← Phase 1
├── quickstart.md            ← Phase 1
├── contracts/
│   └── modulos-analisis.md  ← Phase 1
├── checklists/
│   └── requirements.md
└── tasks.md                 ← Phase 2 (/speckit-tasks)
```

### Código fuente

```text
backend/src/
├── analisis/
│   ├── analizar.py          # junta todo: EntradaAnalisis -> Resultado (Pasos.analizar)
│   ├── participacion.py     # MD-01 a MD-06 y voces cortas (RF-12, RN-01, RN-04)
│   ├── posicion.py          # MD-07 y MD-08: abre y cierra (RF-13)
│   ├── interrupciones.py    # candidatos, tipos y MD-14 a MD-17 (RF-14)
│   ├── indices.py           # RR, BI e IP (RF-16)
│   └── falso.py             # análisis de mentira con los tres ejemplos
├── evaluacion/
│   ├── lectura.py           # lee RTTM, JSON y etiquetas de Audacity
│   ├── metricas.py          # DER, voz, error del % femenino, F1, kappa, bootstrap
│   ├── cronometrar.py       # minutos de proceso por hora de audio (M-09)
│   └── evaluar.py           # un solo script que regenera la tabla 12.1
└── config.py                # umbrales y pesos, en un solo sitio

backend/tests/
├── test_participacion.py    # SC-001
├── test_posicion.py         # SC-001
├── test_interrupciones.py   # SC-002
├── test_indices.py          # SC-003
├── test_analizar.py         # extremo a extremo con casos sintéticos
├── test_evaluacion.py       # métricas
├── test_evaluar.py          # el script de evaluación
└── test_cronometrar.py      # M-09
```

---

## Artefactos de Phase 1

- [research.md](research.md): decisiones técnicas sin NEEDS CLARIFICATION
- [data-model.md](data-model.md): entidades y reglas de cálculo
- [contracts/modulos-analisis.md](contracts/modulos-analisis.md): firmas de los módulos
- [quickstart.md](quickstart.md): escenarios de validación de extremo a extremo

---

## Complejidad

No hay violaciones de la constitución que justificar.
