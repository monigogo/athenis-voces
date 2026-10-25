# Research: Audio y voz

**Rama**: `001-audio-voz` | **Fecha**: 2026-10-24

No quedan elementos NEEDS CLARIFICATION: la pila tecnológica está decidida en D-03 y los
umbrales son valores iniciales de config.py ajustables con la partición de desarrollo (RD-05).

---

## Decisión 1 — Conversión de audio (RF-03)

**Elegido**: pydub (backend en ffmpeg) para convertir cualquier formato de entrada a WAV mono 16 kHz.

**Justificación**: pydub admite mp3, wav, m4a, ogg y flac sin instalar nada extra en el proyecto
si ffmpeg está en el sistema (ya está en el devcontainer). La operación es `audio.set_frame_rate(16000).set_channels(1)` y exportar como WAV. Librería gratuita y de código abierto (LGPL / MIT).

**Alternativas descartadas**:
- soundfile + librosa: soundfile no lee mp3 sin libsndfile; librosa añade dependencias pesadas para
  un paso que solo necesita remuestrear y convertir a mono.

---

## Decisión 2 — Diarización (RF-05)

**Elegido**: pyannote.audio modelo `speaker-diarization-community-1` en local, sin GPU, usando el
token de Hugging Face del entorno (`.env`).

**Justificación**: modelo preentrenado, sin entrenamiento propio, que cumple RNF-20 (CPU) y el
plan, Parte 5.2. Devuelve segmentos por hablante; los solapamientos se calculan a partir de
segmentos que se cruzan en el tiempo. Gratuito y de código abierto (MIT).

**Solapamientos**: se registran solo los de duración ≥ 0,5 s (clarificación 2026-10-24, RD-05).
El umbral vive en `config.solapamiento_registro_desde_segundos`.

**Alternativas descartadas**:
- pyannote-audio versión de pago: no cumple la constitución (punto 4).
- Whisper diarization: transcribe audio, prohibido por constitución punto 6.

---

## Decisión 3 — Propuesta de voz (RF-06)

**Elegido**: inaSpeechSegmenter `GenderIdentifier` preentrenado, sin entrenar ningún modelo.

**Justificación**: librería gratuita (MIT) que devuelve `male`, `female` o `noEnergy` con una
confianza entre 0 y 1. Se aplica segmento a segmento sobre el WAV del hablante. La zona dudosa
(0,35–0,65 [VALIDAR]) convierte la confianza en `indeterminado`. Conforme a RF-06 y RN-03.

**Plan B** (tarea A11 del plan): si inaSpeechSegmenter falla en CPU, se usa el tono medio
(pitch) como clasificador de línea base.

**Alternativas descartadas**:
- Modelos de Hugging Face de clasificación de género de voz: requieren GPU o son demasiado lentos
  en CPU para el requisito de tiempo (SC-007).

---

## Decisión 4 — Selección de fragmentos (RF-07)

**Elegido**: distribución uniforme de los fragmentos a lo largo del audio del hablante
(inicio, mitad, final y los que hagan falta), sin solapamiento entre fragmentos del mismo hablante
(clarificación 2026-10-24).

**Algoritmo**:
1. Recopilar todos los tramos del hablante que no son solapamiento y tienen ≥ 3 s.
2. Ordenarlos cronológicamente.
3. Elegir `config.fragmentos_por_hablante` tramos distribuidos uniformemente por índice
   (índices 0, n//2, n-1, y los intermedios si hace falta más de 3).
4. Recortar cada tramo a entre `fragmento_min_segundos` y `fragmento_max_segundos`.
5. Si hay menos de `fragmentos_por_hablante` tramos válidos, el hablante no aparece en el resultado: no es
   una voz presente y su tiempo cuenta como voz corta (D-18).

**Alternativas descartadas**:
- Selección aleatoria: no reproducible sin semilla fija; complica los tests.
- Tramos más largos primero: sesga hacia el inicio si los tramos largos se concentran allí.

---

## Contrato de datos: sin cambios en contrato.py

Las entidades `Turno`, `Solapamiento`, `Fragmento`, `PropuestaVoz`, `Hablante`,
`HablantesParaConfirmar` y `EstadoAnalisis` ya existen y cubren la feature.

**Única adición al config.py** (no es el contrato de datos): campo
`solapamiento_registro_desde_segundos: float = 0.5` para el umbral mínimo de duración de
solapamiento.
