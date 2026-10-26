# athenis-voces

Mide la **presencia y el protagonismo de las voces femeninas** en grabaciones de audio.
Analiza solo la voz —sin transcribir ni identificar a nadie— y responde a tres preguntas:
¿hay voces femeninas?, ¿qué papel ocupan en la conversación?, ¿se las interrumpe más?

Desarrollado para el reto *Mujeres por la IA Abierta*, dentro de la Comunidad IA de Código Abierto
(SEDIA).

---

## Qué mide

El sistema calcula cuatro dimensiones a partir de la señal de voz:

| Dimensión | Ejemplos de métricas |
|---|---|
| **Presencia** | ¿Hay voces femeninas? Primera intervención, número de voces por grupo |
| **Participación** | Cuota de tiempo y de turnos, turnos largos (>30 s) |
| **Posición** | ¿Quién abre y cierra el episodio? |
| **Respeto del turno** | Interrupciones recibidas y hechas, brecha de interrupción |

Tres índices resumen el resultado: **ratio de representación** (RR), **brecha de interrupción**
(BI) e **índice de protagonismo** (IP, por persona). Sus fórmulas están en
[`docs/01-funcional.md`](docs/01-funcional.md), sección 6.7.

Las etiquetas de voz (femenino, masculino, indeterminado) las confirma siempre una persona;
el modelo solo propone.

## Qué no hace

- No transcribe ni analiza el contenido de lo que se dice.
- No identifica a las personas por su nombre ni por su voz.
- No infiere identidad de género, edad ni origen a partir de la voz.
- No evalúa ni puntúa a personas concretas.
- No funciona en tiempo real ni como aplicación móvil.

---

## Instalación y uso

### Requisitos previos

- **Python 3.11** o superior
- **ffmpeg** instalado en el sistema (`ffmpeg -version` para comprobarlo)
- **Token de Hugging Face** con acceso al modelo de diarización de pyannote, en la variable
  de entorno `HF_TOKEN`
- Aceptar las condiciones de uso del modelo `pyannote/speaker-diarization-community-1` en
  [huggingface.co](https://huggingface.co/pyannote/speaker-diarization-community-1) antes de
  descargarlo

### Instalar el backend

Desde la raíz del repositorio, entra en `backend/`:

```bash
cd backend
```

Dependencias base:

```bash
uv sync
```

Para ejecutar el análisis (incluye pyannote.audio e inaSpeechSegmenter):

```bash
uv sync --group audio
```

Para regenerar la evaluación:

```bash
uv sync --group evaluacion
```

Para instalar todos los grupos a la vez:

```bash
uv sync --all-groups
```

Instalar los hooks de pre-commit (gitleaks, ruff; se hace una sola vez):

```bash
uv run pre-commit install
```

### Ejecutar los tests

Tests rápidos (no requieren modelos descargados):

```bash
uv run pytest tests/ -m "not slow"
```

Tests de integración con modelos reales (requiere el grupo `audio` y los audios descargados):

```bash
uv run pytest tests/
```

### Analizar un audio desde la línea de comandos

El script `analizar_audio.py` ejecuta el pipeline completo (diarización, propuesta de voz,
métricas) sobre un audio y escribe tres ficheros en `<carpeta_de_salida>`, donde `<nombre>`
es el nombre del audio sin extensión y sin el sufijo `.Mix-Headset`:

- `<nombre>.rttm`: quién habla y cuándo (para calcular el DER).
- `<nombre>.json`: el resultado del contrato, con las voces confirmadas con la propuesta del
  modelo (origen «modelo»). Solo para evaluación; en la web las confirma una persona.
- `<nombre>.tiempo.json`: duración del audio y segundos del proceso completo.

```bash
cd backend
uv run scripts/analizar_audio.py <ruta_del_audio> <carpeta_de_salida>
```

Si no hay voces suficientes o un paso falla, queda el `.rttm` pero no el `.json`, y el
motivo sale por la salida de error estándar.

---

## Datos

Los audios de evaluación no están en el repositorio (regla 7 de la constitución). Se
descargan con:

```bash
scripts/descargar_datos.sh
```

El script baja las 7 reuniones de AMI y las anotaciones de BUT a `datos/ami/` (unos 430 MB
en total), comprueba la huella SHA-256 de cada audio y fija las anotaciones a un commit
concreto. Es idempotente: lo que ya está bien no se vuelve a bajar.

| Fuente | Contenido | Licencia |
|---|---|---|
| [Corpus AMI](https://groups.inf.ed.ac.uk/ami/corpus/) | Audio de reuniones en inglés (Mix-Headset, WAV mono 16 kHz) | [CC BY 4.0](https://groups.inf.ed.ac.uk/ami/corpus/license.shtml) |
| [Anotaciones de BUT](https://github.com/BUTSpeechFIT/AMI-diarization-setup) | Quién habla y cuándo en cada reunión (RTTM) | Apache-2.0 |
| Grabaciones propias del equipo | 2 conversaciones en español, con consentimiento por escrito | Solo para este reto |
| Sesión del Congreso | Una sesión pública, para la demo | Reutilización citando la fuente [pendiente de validar] |

Los audios nunca entran en el repositorio. Las etiquetas de interrupción anotadas por el
equipo sí están, en `evaluacion/etiquetas/`, sin audio, texto ni nombres.

---

## Dependencias principales y sus licencias

La tabla completa y verificada se obtiene ejecutando:

```bash
scripts/listar_licencias.sh
```

Las dependencias declaradas en [`backend/pyproject.toml`](backend/pyproject.toml) son:

| Paquete | Versión | Grupo | Licencia |
|---|---|---|---|
| pydantic | ≥2.14.1 | base | pendiente (ejecutar `listar_licencias.sh`) |
| pyannote.audio | ≥4.0 | audio | pendiente |
| inaSpeechSegmenter | ≥0.8 | audio | pendiente |
| torch | ==2.11.0 | audio | pendiente |
| torchaudio | ==2.11.0 | audio | pendiente |
| pyannote-metrics | ≥4.2.0 | evaluacion | pendiente |
| pytest | ≥8.0 | dev | pendiente |
| ruff | ≥0.6 | dev | pendiente |
| bandit | ≥1.9.4 | dev | pendiente |
| pip-audit | ≥2.10.1 | dev | pendiente |
| pip-licenses | ≥5.5.5 | dev | pendiente |
| pre-commit | ≥4.7.0 | dev | pendiente |

El modelo de diarización de pyannote se distribuye bajo licencia **CC-BY-4.0**
(véase [`docs/01-funcional.md`](docs/01-funcional.md), sección 10.4).

La versión de PyTorch está fijada a 2.11.0 porque la GPU V100S (capacidad 7.0) no es
compatible con versiones posteriores debido a su cuDNN (restricción C6 del funcional).

**Software de terceros no abierto: las librerías CUDA de NVIDIA.** PyTorch, TensorFlow e
inaSpeechSegmenter instalan las librerías CUDA de NVIDIA (`nvidia-*-cu12` y `cuda-toolkit`), que
son gratuitas pero tienen licencia privativa de NVIDIA. Solo sirven para usar la GPU que cede
OVHcloud, y por eso entran en la excepción de la regla 4 de la constitución (decisión D-22 del
funcional). `listar_licencias.sh` las marca como «permitida (D-22)»; cualquier otra licencia
cerrada lo hace fallar. El código del proyecto sigue bajo licencia MIT.

---

## Ética y uso responsable

El marco ético completo está en [`docs/01-funcional.md`](docs/01-funcional.md), **sección 10**.

Algunas decisiones de diseño relevantes:

- **La voz percibida no es la identidad de género.** El sistema usa la autopresentación
  pública como referencia y ofrece siempre la opción «indeterminado».
- **Supervisión humana obligatoria.** Ningún resultado se muestra sin que una persona haya
  confirmado las etiquetas de voz.
- **Modo manual** (RF-08): desactiva toda propuesta automática. El modo manual reduce la
  exposición legal del sistema como posible sistema de alto riesgo bajo el Reglamento (UE)
  2024/1689 de Inteligencia Artificial (análisis en la sección 4.3 del funcional).
- **Sin identificación:** la diarización agrupa voces dentro del audio; no identifica a
  ninguna persona ni envía el audio fuera de la infraestructura propia.
- **Sesgo medido, no supuesto:** el error del clasificador de voz se publica por grupo, con
  intervalo de confianza.

### Usos permitidos y prohibidos

Se recomienda la política de uso descrita en la **sección 10.6** del funcional.

**Usos permitidos:** auditoría agregada de contenidos, investigación, formación y
sensibilización.

**Usos prohibidos:** evaluar, puntuar o seleccionar a personas concretas (contratación,
promoción, retribución); identificar hablantes; inferir orientación sexual, identidad de
género u otros atributos sensibles; vigilar a empleadas o empleados; publicar resultados
por persona sin su consentimiento.

Una licencia abierta no puede restringir usos. Esta política se aplica a la instancia que
opera el equipo y se recomienda a quienes reutilicen el sistema.

---

## Hoja de ruta

Lo que figura en [`docs/01-funcional.md`](docs/01-funcional.md), sección 1.3, como trabajo
fuera del MVP actual:

- Interfaz en catalán, euskera y gallego
- Análisis de vídeo
- Análisis interseccional
- Análisis en directo
- Comparar episodios y exportar resultados (JSON y CSV)
- Servidor MCP público

---

## Contribuir

Consulta [`CONTRIBUTING.md`](CONTRIBUTING.md) para el flujo de ramas, convención de
commits, estructura del proyecto y cómo pasar las comprobaciones locales.

## Licencia

[MIT](LICENSE)
