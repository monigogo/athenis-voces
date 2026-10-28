# Plan de implementación: Producto (servidor HTTP de la API interna)

**Rama**: `feat/vani/api-servidor` | **Fecha**: 2026-10-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification de `specs/003-producto/spec.md`

---

## Resumen

Servir las rutas de la sección 9.3 con FastAPI para que la web use el núcleo que ya existe:
`pipeline.py` y los módulos reales de las features 001 y 002. Primero, un camino mínimo de punta a
punta: salud, subir un audio, estado, hablantes para confirmar, fragmento de audio, confirmación y
resultado. Después, ejemplos precalculados, modo manual, retención de 24 h y demo pública sin
subidas. Al final, la web deja de simular y llama a estas rutas.

El servidor no calcula nada: recibe, valida, encola y guarda el estado. No modifica el contrato de
datos ni `pipeline.py`.

La responsable de la 003 es la persona C. Este plan se prepara en la rama `feat/vani/api-servidor`,
con el acuerdo del equipo.

---

## Contexto técnico

**Lenguaje / versión**: Python 3.11 (backend) y TypeScript 5.7 (web)

**Dependencias principales**:
- `fastapi`, `uvicorn` y `python-multipart` (dependencias base del backend)
- `httpx` (grupo `dev`, para el `TestClient` de las pruebas)
- ffmpeg y ffprobe del sistema, que ya se usan en `audio/preparar.py`
- en la web, `openapi-typescript` (desarrollo) para generar los tipos (FR-015)

**Almacenamiento**: registro en memoria; audios y WAV en `CARPETA_TRABAJO`, fuera del repositorio,
borrados a las 24 h [VALIDAR]

**Testing**: pytest con el `TestClient` de FastAPI, un `Pasos` falso y WAV generados en `tmp_path`;
vitest con `fetch` simulado en la web

**Plataforma**: Linux con la GPU V100S de OVHcloud para el análisis real; las pruebas, sin GPU

**Tipo de proyecto**: web, con backend (`backend/src/api/`) y frontend (`frontend/src/services/`)

**Objetivo de rendimiento**: las rutas que no analizan responden en menos de 200 ms; un ejemplo
precalculado se ve en 2 s o menos (SC-001)

**Restricciones**: tipos solo de `contrato.py`; subida según RNF-10; fragmentos de 15 s como máximo
(9.3); nada de audio en el repositorio (RD-04)

**Escala**: un solo proceso, un análisis a la vez en la GPU; pocas personas a la vez en la demo

---

## Verificación de la constitución

| Punto | Verificación | Estado |
|-------|-------------|--------|
| 1. Manda el funcional | Solo las 8 rutas de 9.3. Reintentar (FR-004) queda fuera porque 9.3 no tiene ruta para eso | ✅ |
| 2. TDD obligatorio | Cada tarea de código va detrás de su prueba, que tiene que fallar antes | GATE |
| 3. Contrato único | Las rutas reciben y devuelven tipos de `contrato.py`, que no cambia. Los metadatos de los ejemplos quedan como punto abierto | ✅ |
| 4. Todo gratuito | FastAPI, uvicorn, python-multipart y httpx (MIT y BSD); openapi-typescript (MIT) | ✅ |
| 5. uv solo en backend/ | Python con `uv` en `backend/`; la web con `pnpm` en `frontend/` | ✅ |
| 6. Solo analiza la voz | El servidor no transcribe: reutiliza el pipeline existente | ✅ |
| 7. Sin audios en repo | `CARPETA_TRABAJO` en el directorio temporal; las pruebas generan sus WAV en `tmp_path` | ✅ |
| 8. Tres opciones de confirmación | `POST /confirmacion` recibe `Confirmacion`, con `femenino`, `masculino` o `indeterminado` | ✅ |
| 9. Reuniones de prueba solo miden | El servidor no ajusta nada; los ejemplos no salen de la partición de prueba | ✅ |
| 10. Primero los Must | Camino mínimo (RF-01, RF-04, RF-07, RF-17, RF-18) antes que ejemplos, modo manual y retención | ✅ |
| 11. Las 8 fases | Spec aclarada el 27 oct; este fichero es la fase de plan; la implementación espera a `tasks.md` y al visto bueno | ✅ |

**GATE TDD**: ninguna tarea de código empieza sin su prueba escrita y fallando (constitución 2).

---

## Estructura del proyecto

### Documentación de esta feature

```text
specs/003-producto/
├── plan.md             ← este fichero
├── research.md         ← Phase 0
├── data-model.md       ← Phase 1
├── quickstart.md       ← Phase 1
├── contracts/
│   └── api-http.md     ← Phase 1
├── checklists/
│   └── requirements.md
└── tasks.md            ← Phase 2
```

### Código fuente

```text
backend/
├── ejemplos/                 # Resultado en JSON de los ejemplos precalculados
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py            # crear_app(...) y las rutas de 9.3
│   │   ├── ajustes.py        # CARPETA_TRABAJO, EJEMPLOS_DIR y DEMO_PUBLICA desde el entorno
│   │   ├── registro.py       # registro en memoria de los análisis
│   │   ├── cola.py           # ejecutor de un solo trabajador y las dos fases del pipeline
│   │   ├── subida.py         # tamaño, tipo real por bytes, duración con ffprobe (RNF-10)
│   │   ├── fragmento.py      # recorte de un WAV de 15 s como máximo
│   │   ├── retencion.py      # borrar_caducados (RF-23)
│   │   └── pasos_reales.py   # Pasos con los módulos de 001 y 002
│   └── config.py             # + subida_max_bytes, subida_max_segundos, retencion_segundos
└── tests/
    ├── test_api_salud.py
    ├── test_api_subida.py
    ├── test_api_recorrido.py   # estado, hablantes, confirmación, resultado
    ├── test_api_fragmento.py
    ├── test_api_ejemplos.py
    ├── test_api_modo_manual.py
    └── test_api_retencion.py

frontend/src/
├── services/api.ts           # llamadas reales en vez de la simulación
├── services/audioPlayer.ts   # reproduce los fragmentos que da el servidor
└── types/api.ts              # generado desde /openapi.json (FR-015)
```

---

## Artefactos de Phase 1

- [research.md](research.md): las 12 decisiones técnicas, sin NEEDS CLARIFICATION
- [data-model.md](data-model.md): registro interno, estados y reglas de validación
- [contracts/api-http.md](contracts/api-http.md): rutas, entradas, salidas y códigos de error
- [quickstart.md](quickstart.md): cómo validar de punta a punta

---

## Puntos abiertos para el equipo

- Confirmar los [VALIDAR]: 200 MB, 60 min, retención de 24 h y demo pública sin subidas (D-08).
- Metadatos de los ejemplos (nombre, origen, licencia): fuera del contrato hasta que lo acuerden las
  tres (constitución 3).
- Ejemplos reales: IB4002 e IB4010 del corpus AMI (partición de desarrollo), con etiquetas de voz del
  modelo, sin confirmación humana; sin audio.

---

## Complejidad

No hay violaciones de la constitución que justificar.
