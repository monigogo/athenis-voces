# Contrato de módulos: análisis y evaluación

**Referencia**: `backend/src/pipeline.py`, dataclass `Pasos`, y `backend/src/analisis/`.

Todas las funciones reciben `config: Config = CONFIG` como último parámetro.

---

## `analisis/analizar.py`

```python
def analizar(entrada: EntradaAnalisis, config: Config = CONFIG) -> Resultado: ...
```

Cumple la firma `Pasos.analizar`. Pone `id_analisis` provisional (`"pendiente"`); el pipeline pone el
de verdad. Si el cálculo falla, el pipeline lo captura y deja el análisis en «error» (FR-014).

## `analisis/participacion.py`

```python
def turnos_que_cuentan(entrada, senales=()) -> list[Turno]
def por_hablante(entrada, senales=(), config=CONFIG) -> list[ParticipacionHablante]
def por_grupo(entrada, senales=(), config=CONFIG) -> list[ParticipacionGrupo]
def presencia(entrada, senales=(), config=CONFIG) -> Presencia
```

## `analisis/posicion.py`

```python
def quien_abre(entrada, config=CONFIG) -> int | None
def quien_cierra(entrada, config=CONFIG) -> int | None
```

Devuelven `None` si ningún turno dura más de 5 s.

## `analisis/interrupciones.py`

```python
def detectar(entrada, config=CONFIG) -> list[Interrupcion]
def por_hablante(entrada, interrupciones, config=CONFIG) -> list[InterrupcionesHablante]
def por_grupo(entrada, interrupciones, config=CONFIG) -> list[InterrupcionesGrupo]
```

`detectar` devuelve también las señales de escucha, con `tipo.cuenta_como_interrupcion` en falso.

## `analisis/indices.py`

```python
def ratio_representacion(t_f, t_e, n_f, n_e) -> float | None
def brecha_interrupcion(i_f, t_f, i_m, t_m, config=CONFIG) -> float | None
def de_grupo(t_f, t_m, n_f, n_m, i_f, i_m, config=CONFIG) -> list[Indice]
def protagonismo(segundos, abre, cierra, turnos_largos, config=CONFIG) -> dict[int, float]
```

`None` es «no aplicable» (RN-13).

## `evaluacion/evaluar.py`

```text
PYTHONPATH=src uv run --group evaluacion python -m evaluacion.evaluar --salidas <carpeta>
```

| Opción | Descripción |
|--------|-------------|
| `--salidas` | Carpeta con `<reunión>.rttm` y `<reunión>.json` (obligatoria) |
| `--ami` | Carpeta con los RTTM de referencia de AMI |
| `--etiquetas` | Carpeta con las etiquetas de Audacity (`_A.txt`, `_C.txt`, `_referencia.txt`) |

Escribe la tabla 12.1 por pantalla. Devuelve 2 si una carpeta no existe. Lo que falta no se evalúa y
no cuenta en n.
