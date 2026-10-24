# Modelo de datos: Audio y voz

**Fuente de verdad de los tipos**: `backend/src/contrato.py` (VERSION_CONTRATO = "0.2").
Este documento describe las entidades que usa la feature y las reglas de negocio que las rigen.

---

## Entidades existentes que usa esta feature

### Audio preparado *(resultado de `audio/preparar.py`)*

No es un tipo Pydantic: es un fichero WAV que `preparar` escribe en disco.

| Campo | Tipo | Regla |
|-------|------|-------|
| ruta WAV | `Path` | `{carpeta}/{id_analisis}.wav` |
| duración | `float` (segundos) | > 0; dentro de ± 0,1 s de la entrada (RF-03) |
| formato | WAV mono 16 kHz | frecuencia en `config.frecuencia_muestreo` |

### Turno (`contrato.Turno`)

Tramo continuo en el que habla un hablante.

| Campo | Tipo | Regla |
|-------|------|-------|
| `hablante` | `int ≥ 1` | Numerado desde 1; no identifica a nadie (RN-10) |
| `inicio` | `float ≥ 0` | Segundos con decimales |
| `fin` | `float > inicio` | Segundos con decimales |

### Solapamiento (`contrato.Solapamiento`)

Tramo en que hablan dos o más hablantes a la vez.

| Campo | Tipo | Regla |
|-------|------|-------|
| `hablantes` | `list[int ≥ 1]` | Mínimo 2 hablantes distintos |
| `inicio` | `float ≥ 0` | Segundos con decimales |
| `fin` | `float > inicio` | Segundos con decimales |

**Regla de registro** (clarificación 2026-10-24): solo se registran solapamientos con
`fin - inicio ≥ config.solapamiento_registro_desde_segundos` (0,5 s por defecto).

### PropuestaVoz (`contrato.PropuestaVoz`)

Propuesta del modelo para un hablante. Solo existe en modo asistido.

| Campo | Tipo | Regla |
|-------|------|-------|
| `etiqueta` | `EtiquetaVoz` | `femenino`, `masculino` o `indeterminado` |
| `confianza` | `float [0, 1]` | Probabilidad devuelta por inaSpeechSegmenter |

**Regla de zona dudosa** (RF-06): si `config.zona_dudosa_min ≤ confianza ≤ config.zona_dudosa_max`
(0,35–0,65 [VALIDAR]), la etiqueta es `indeterminado` independientemente de lo que diga el modelo.

### Fragmento (`contrato.Fragmento`)

Muestra de la voz de un hablante para escucharla al confirmar.

| Campo | Tipo | Regla |
|-------|------|-------|
| `inicio` | `float ≥ 0` | Segundos con decimales |
| `fin` | `float > inicio` | Segundos con decimales |

**Reglas de fragmento** (RF-07, clarificaciones 2026-10-24):
- Duración entre `config.fragmento_min_segundos` (3 s) y `config.fragmento_max_segundos` (5 s).
- Solo tramos sin solapamiento del hablante.
- Mínimo `config.fragmentos_por_hablante` (3) por hablante presente.
- Distribuidos uniformemente a lo largo del audio del hablante (inicio, mitad, final).
- Sin solapamiento entre fragmentos del mismo hablante (ningún segundo compartido).

### Hablante (`contrato.Hablante`)

Un hablante tal como llega a la pantalla Confirmar voces.

| Campo | Tipo | Regla |
|-------|------|-------|
| `hablante` | `int ≥ 1` | Mismo número que en los turnos |
| `segundos_habla` | `float ≥ 0` | Suma de `fin - inicio` de sus turnos |
| `propuesta` | `PropuestaVoz \| None` | `None` en modo manual (RF-08) |
| `fragmentos` | `list[Fragmento]` | ≥ 3 fragmentos si el hablante es presente |

**Hablante presente** (RN-01 [VALIDAR]): `segundos_habla ≥ config.presencia_desde_segundos` (10 s).
Los hablantes no presentes no aparecen en esta lista; su tiempo se acumula en
`Resultado.segundos_voces_cortas` (D-15).

### HablantesParaConfirmar (`contrato.HablantesParaConfirmar`)

Respuesta que devuelve la fase 1 del pipeline.

| Campo | Tipo | Regla |
|-------|------|-------|
| `version_contrato` | `str` | Debe ser VERSION_CONTRATO |
| `id_analisis` | `str` | No vacío |
| `hablantes` | `list[Hablante]` | Sin hablantes repetidos |

---

## Campo nuevo en config.py

| Campo | Valor por defecto | Referencia |
|-------|-------------------|------------|
| `solapamiento_registro_desde_segundos` | `0.5` | Clarificación 2026-10-24 |

Este campo se añade a `backend/src/config.py` junto a los demás umbrales de solapamiento.
No modifica `contrato.py` (constitución, punto 3).

---

## Modo del análisis

El campo `modo_manual: bool` viaja como parámetro del pipeline (`preparar_para_confirmar`),
no como campo del contrato de datos (clarificación 2026-10-24). La API lo recibe al crear un
análisis y lo pasa al pipeline. Internamente, si `modo_manual=True`, `proponer_voz` no se ejecuta
y `propuesta` es `None` para todos los hablantes (RF-08).

---

## Diagrama de flujo de datos (fase 1)

```
audio (mp3/wav/…) ──► preparar() ──► {WAV 16 kHz}
                                          │
                              ┌───────────┴──────────────┐
                              ▼                           ▼
                         diarizar()               (si asistido)
                              │                   proponer_voz()
                    ┌─────────┴─────────┐              │
                    ▼                   ▼               ▼
               [Turno]          [Solapamiento]   {hablante: PropuestaVoz}
                    │                   │
                    └──────┬────────────┘
                           ▼
                  elegir_fragmentos()
                           │
                           ▼
               {hablante: [Fragmento]}
                           │
                    ───────┴────────────────────────────────────
                    Pipeline ensambla HablantesParaConfirmar
```
