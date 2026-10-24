# Guía de validación: Audio y voz

Cómo verificar que la feature funciona de extremo a extremo.

**Prerrequisito**: los audios de evaluación descargados con `scripts/descargar_datos.sh`
(constitución, punto 7). No se suben al repositorio.

---

## 1. Instalar dependencias

```bash
cd backend
uv sync
```

Para los modelos de audio (primera ejecución, descarga modelos de Hugging Face):

```bash
uv run python -c "from audio.diarizacion import diarizar; print('ok')"
uv run python -c "from voz.clasificador import proponer_voz; print('ok')"
```

---

## 2. Ejecutar los tests unitarios (TDD)

```bash
cd backend
uv run pytest tests/test_preparar.py tests/test_diarizacion.py \
    tests/test_fragmentos.py tests/test_clasificador.py -v
```

Todos deben pasar antes de tocar ningún módulo real.

---

## 3. Validar preparación del audio (SC-001)

Pasa un fragmento de 5 min de la reunión IB4002 y comprueba que el WAV resultante tiene
la duración correcta (± 0,1 s) y el formato esperado.

```bash
cd backend
uv run python - <<'EOF'
from pathlib import Path
from audio.preparar import preparar

entrada = Path("../data/IB4002_fragmento_5min.mp3")   # descargado con descargar_datos.sh
destino = Path("/tmp/ib4002_prep.wav")
duracion = preparar(entrada, destino)
print(f"Duración: {duracion:.2f} s")

import wave
with wave.open(str(destino)) as w:
    print(f"Canales: {w.getnchannels()} (esperado: 1)")
    print(f"Frecuencia: {w.getframerate()} Hz (esperado: 16000)")
EOF
```

**Resultado esperado**: `Canales: 1`, `Frecuencia: 16000 Hz`, duración ± 0,1 s de la entrada.

---

## 4. Validar diarización (SC-002 — partición de prueba)

```bash
cd backend
uv run python - <<'EOF'
from pathlib import Path
from audio.preparar import preparar
from audio.diarizacion import diarizar

wav = Path("/tmp/ib4002_prep.wav")
turnos, solapamientos = diarizar(wav)
hablantes = {t.hablante for t in turnos}
print(f"Hablantes detectados: {sorted(hablantes)}")
print(f"Turnos: {len(turnos)}")
print(f"Solapamientos (≥ 0,5 s): {len(solapamientos)}")
for s in solapamientos[:3]:
    print(f"  {s.hablantes} {s.inicio:.1f}–{s.fin:.1f} s ({s.fin-s.inicio:.2f} s)")
EOF
```

**Resultado esperado**: ≥ 2 hablantes, turnos con formato `Hablante n`, solapamientos todos ≥ 0,5 s.

---

## 5. Validar propuesta de voz (SC-003 / SC-004)

Usa el audio AMI EN2002a (sexo de referencia conocido por el código del corpus).

```bash
cd backend
uv run python - <<'EOF'
from pathlib import Path
from audio.preparar import preparar
from audio.diarizacion import diarizar
from voz.clasificador import proponer_voz

wav = Path("/tmp/en2002a_prep.wav")   # preparar primero si no existe
turnos, _ = diarizar(wav)
propuestas = proponer_voz(wav, turnos)
for h, p in sorted(propuestas.items()):
    print(f"Hablante {h}: {p.etiqueta} (confianza {p.confianza:.2f})")
EOF
```

**Resultado esperado**: cada hablante tiene etiqueta y confianza ∈ [0, 1]; los de confianza
entre 0,35 y 0,65 tienen etiqueta `indeterminado`.

---

## 6. Validar fragmentos (SC-006)

```bash
cd backend
uv run python - <<'EOF'
from pathlib import Path
from audio.diarizacion import diarizar
from audio.fragmentos import elegir_fragmentos
from config import CONFIG

wav = Path("/tmp/ib4002_prep.wav")
turnos, solapamientos = diarizar(wav)
fragmentos = elegir_fragmentos(turnos, solapamientos)
for h, frags in sorted(fragmentos.items()):
    duraciones = [f.fin - f.inicio for f in frags]
    print(f"Hablante {h}: {len(frags)} fragmentos, "
          f"duraciones {[f'{d:.1f}s' for d in duraciones]}")
    assert len(frags) >= CONFIG.fragmentos_por_hablante, "faltan fragmentos"
    for f in frags:
        assert CONFIG.fragmento_min_segundos <= (f.fin - f.inicio) <= CONFIG.fragmento_max_segundos
print("OK")
EOF
```

**Resultado esperado**: cada hablante presente tiene ≥ 3 fragmentos de 3–5 s.

---

## 7. Validar modo manual (SC-005)

```bash
cd backend
uv run pytest tests/test_pipeline.py -k "manual" -v
```

**Resultado esperado**: con `modo_manual=True`, el clasificador no se ejecuta y `propuesta` es
`None` para todos los hablantes.

---

## 8. Recorrido completo con el falso de análisis

```bash
cd backend
uv run pytest tests/ -v
```

Todos los tests deben pasar. El falso de análisis (`analisis/falso.py`) cubre la fase 2 mientras
el análisis real no está listo.
