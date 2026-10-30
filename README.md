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
(BI) e **índice de protagonismo** (IP, por persona). Sus fórmulas se explican en la
pantalla Metodología de la aplicación.

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

### Desplegar con Docker

Levanta la web y la API con un solo comando. Necesita Docker con Compose y el token de
Hugging Face descrito en los requisitos previos:

```bash
cp .env.example .env              # y rellena HF_TOKEN
docker compose up -d --build
```

La web queda en `http://localhost:8080`. La API no se publica fuera: la web la alcanza en
`/api` a través de nginx. El audio subido y los modelos descargados se guardan en volúmenes de
Docker, nunca dentro de las imágenes.

En un servidor con GPU NVIDIA (con NVIDIA Container Toolkit instalado):

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

### Requisitos previos

- **Python 3.11** o superior
- **ffmpeg** instalado en el sistema (`ffmpeg -version` para comprobarlo)
- **Token de Hugging Face** con acceso al modelo de diarización de pyannote, en la variable
  de entorno `HF_TOKEN`
- Aceptar las condiciones de uso del modelo `pyannote/speaker-diarization-community-1` en
  [huggingface.co](https://huggingface.co/pyannote/speaker-diarization-community-1) antes de
  descargarlo

### Abrir el proyecto en VS Code: con GPU o solo con CPU

El proyecto trae dos entornos de desarrollo listos (extensión **Dev Containers** de VS Code). Al
abrir la carpeta, **Dev Containers: Reopen in Container** pregunta cuál usar:

| Entorno | Cuándo | Qué cambia |
| --- | --- | --- |
| **athenis-voces · CPU (sin GPU)** | No tienes tarjeta NVIDIA | Todo funciona; analizar un audio es más lento |
| **athenis-voces · GPU NVIDIA** | Tienes una tarjeta NVIDIA | El análisis usa la GPU (`DISPOSITIVO=cuda`) |

Los dos traen Python 3.12, uv, Node 22, pnpm y ffmpeg, y abren los puertos 8000 (API) y 5173 (web)
hacia tu navegador. Comparten la caché de descargas: PyTorch y TensorFlow ocupan varios GB y no se
vuelven a bajar al cambiar de entorno. Para cambiar: **Dev Containers: Reopen Folder Locally** y
otra vez **Reopen in Container**, eligiendo el otro.

**Para el entorno con GPU**, antes de abrirlo:

1. El **driver de NVIDIA** de tu ordenador tiene que admitir CUDA 12.6 (lo que usa PyTorch 2.11).
   La imagen no trae CUDA: las librerías vienen dentro de PyTorch; el ordenador solo pone el driver.
2. **Docker tiene que ver la GPU**: en Windows, Docker Desktop con WSL 2; en Linux, el NVIDIA
   Container Toolkit. Compruébalo en un terminal de tu ordenador (fuera de VS Code):

   ```bash
   docker run --rm --gpus all ubuntu nvidia-smi
   ```

   Si sale la tabla con tu tarjeta, ya puedes usar el entorno con GPU. Si da un error, usa el de CPU.

Dentro del entorno con GPU, tras instalar el grupo `audio`, comprueba que PyTorch la ve:

```bash
cd backend
uv run python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

Tiene que acabar en `True`. Cada entorno ya fija `DISPOSITIVO`; en tu `.env`, déjalo en `auto` o
quítalo.

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

### Arrancar el servidor de la API

El servidor sirve las rutas de la sección 9.3 del funcional (subir un audio, estado, hablantes,
fragmentos, confirmación, resultado, ejemplos y salud). Necesita el grupo `audio` y ffmpeg:

```bash
cd backend
uv sync --group audio
uv run --env-file ../.env uvicorn api.app:app --app-dir src --port 8000
```

- `--env-file` carga `HF_TOKEN` y el resto de variables de `.env` (ver `.env.example`).
- Arranca con **un solo proceso**, sin `--workers`: el registro de análisis vive en su memoria.
- Las rutas y sus tipos se ven en `http://localhost:8000/docs`.
- Variables opcionales: `CARPETA_TRABAJO` (por defecto, una carpeta del directorio temporal del
  sistema), `EJEMPLOS_DIR` (por defecto, `backend/ejemplos`) y `DEMO_PUBLICA=1` para no admitir
  subidas.

Límites provisionales, pendientes de validar por el equipo: 200 MB y 60 min por audio, y borrado
del audio a las 24 h de subirlo.

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
| Sesión del Congreso | Una sesión pública, para la demo | Reutilización citando la fuente y la fecha de la última actualización (Aviso legal del Congreso, comprobado el 26 oct 2026); vídeos de sesiones de uso libre; sin grabación de interpretación simultánea |

Los audios nunca entran en el repositorio. Las etiquetas de interrupción anotadas por el
equipo sí están, en `evaluacion/etiquetas/`, sin audio, texto ni nombres.

Los ejemplos de la demo (`backend/ejemplos/`) son resultados del sistema sobre las reuniones IB4002
e IB4010 del [corpus AMI](https://groups.inf.ed.ac.uk/ami/corpus/) (CC BY 4.0): resultados derivados,
sin audio.


## Ética y uso responsable


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

Trabajo fuera del MVP actual:

- Interfaz en catalán, euskera y gallego
- Análisis de vídeo
- Análisis interseccional
- Análisis en directo
- Comparar episodios y exportar resultados (JSON y CSV)

---

## Licencia

[MIT](LICENSE)
