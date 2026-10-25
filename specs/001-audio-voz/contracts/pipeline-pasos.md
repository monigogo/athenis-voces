# Contrato de módulos: firmas del pipeline

Los cuatro módulos nuevos deben cumplir exactamente estas firmas para enchufarse en
`backend/src/pipeline.py` a través del dataclass `Pasos`. Cualquier desviación rompe el pipeline.

**Referencia**: `backend/src/pipeline.py`, dataclass `Pasos`.

---

## `audio/preparar.py`

```python
def preparar(audio: Path, destino: Path) -> float:
    ...
```

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `audio` | `Path` | Ruta al audio de entrada (mp3, wav, m4a, ogg, flac) |
| `destino` | `Path` | Ruta donde escribir el WAV resultante |
| **retorno** | `float` | Duración en segundos del audio preparado |

**Postcondiciones**:
- `destino` existe y es WAV mono a `config.frecuencia_muestreo` Hz (16 000).
- `abs(retorno - duración_entrada) ≤ config.tolerancia_duracion_segundos` (0,1 s).
- Lanza cualquier excepción si el audio no se puede leer o convertir; el pipeline la captura.

---

## `audio/diarizacion.py`

```python
def diarizar(wav: Path) -> tuple[list[Turno], list[Solapamiento]]:
    ...
```

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `wav` | `Path` | WAV mono 16 kHz producido por `preparar` |
| **retorno** | `tuple` | Lista de turnos y lista de solapamientos |

**Postcondiciones**:
- Todos los `Turno` y `Solapamiento` son instancias válidas de `contrato.py`.
- Se incluyen todos los solapamientos detectados, sin filtrar por duración (el filtro de 0,3 s es de la persona B).
- Los hablantes se numeran desde 1 (`Hablante n`); nunca se identifica a nadie.
- Si el audio no tiene ninguna voz, o solo una, lanza excepción con el motivo.
- Lanza cualquier excepción ante fallo técnico; el pipeline la captura.

---

## `voz/clasificador.py`

```python
def proponer_voz(wav: Path, turnos: list[Turno]) -> dict[int, PropuestaVoz]:
    ...
```

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `wav` | `Path` | WAV mono 16 kHz |
| `turnos` | `list[Turno]` | Turnos devueltos por `diarizar` |
| **retorno** | `dict[int, PropuestaVoz]` | Propuesta por número de hablante |

**Postcondiciones**:
- El dict contiene exactamente los números de hablante presentes en `turnos`.
- `PropuestaVoz.etiqueta` es `indeterminado` si la confianza cae en la zona dudosa
  (`config.zona_dudosa_min` ≤ confianza ≤ `config.zona_dudosa_max`).
- `PropuestaVoz.confianza` ∈ [0, 1].
- Solo se llama en modo asistido; en modo manual el pipeline pasa `{}` directamente (RF-08).

---

## `audio/fragmentos.py`

```python
def elegir_fragmentos(
    turnos: list[Turno], solapamientos: list[Solapamiento]
) -> dict[int, list[Fragmento]]:
    ...
```

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `turnos` | `list[Turno]` | Turnos devueltos por `diarizar` |
| `solapamientos` | `list[Solapamiento]` | Solapamientos devueltos por `diarizar` |
| **retorno** | `dict[int, list[Fragmento]]` | Fragmentos por número de hablante |

**Postcondiciones**:
- Solo aparecen hablantes con `segundos_habla ≥ config.presencia_desde_segundos` (10 s).
- Hablantes con menos de `config.fragmentos_por_hablante` (3) tramos válidos no aparecen en el dict
  (no son voces presentes: el pipeline no los pasa a confirmación y su tiempo cuenta como voz corta, D-18).
- Cada `Fragmento` proviene de un tramo sin solapamiento del hablante.
- Duración de cada fragmento: `[config.fragmento_min_segundos, config.fragmento_max_segundos]`.
- Los fragmentos de un mismo hablante no se solapan entre sí (clarificación 2026-10-24).
- Los fragmentos están distribuidos uniformemente a lo largo del audio del hablante
  (clarificación 2026-10-24).
