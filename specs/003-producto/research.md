# Research: Producto (servidor HTTP de la API interna)

**Rama**: `feat/vani/api-servidor` | **Fecha**: 2026-10-27

No quedan elementos NEEDS CLARIFICATION. Los límites, la retención y las subidas de la demo pública
tienen respuestas provisionales ([VALIDAR]) en la sección «Aclaraciones» de la spec. Este plan cubre el
servidor HTTP de la sección 9.3 y su conexión con la web; las pantallas ya existen.

---

## Decisión 1: FastAPI, con uvicorn y python-multipart

**Elegido**: FastAPI para las rutas, uvicorn para servirlas y python-multipart para recibir el audio.

**Justificación**: el funcional ya lo fija (9.3: «la descripción OpenAPI que publica FastAPI es la
fuente de los tipos del frontend», RD-02). FastAPI usa pydantic, así que `contrato.py` sirve tal cual
como modelos de entrada y salida, sin copiar ningún tipo. Las tres son de código abierto (MIT y BSD;
constitución 4).

Para las pruebas hace falta `httpx`, porque el `TestClient` de FastAPI lo necesita (BSD; grupo `dev`).

**Alternativas descartadas**:
- Flask o la biblioteca estándar: habría que escribir a mano la validación y el OpenAPI.

---

## Decisión 2: Ningún tipo nuevo en el contrato

**Elegido**: cada ruta recibe y devuelve tipos de `contrato.py`, que no se toca (constitución 3):

| Ruta | Devuelve |
|------|----------|
| POST /analisis | `EstadoAnalisis` («Identificador y estado») |
| GET /analisis/{id} | `EstadoAnalisis` |
| GET /analisis/{id}/hablantes | `HablantesParaConfirmar` |
| POST /analisis/{id}/confirmacion | recibe `Confirmacion`, devuelve `EstadoAnalisis` |
| GET /analisis/{id}/resultado | `Resultado` |
| GET /analisis/{id}/fragmento | audio WAV, no JSON |
| GET /ejemplos | `list[Resultado]` |
| GET /salud | `EstadoServicio` (ver abajo) |

**Justificación**: rehacer el contrato exige el acuerdo de las tres.

**Puntos abiertos para el equipo**:
- El nombre, el origen y la licencia de cada ejemplo (entidad «Ejemplo precalculado» de la spec) no
  están en el contrato. Por ahora la web los conserva por `id_analisis`. Llevarlos por la API exige
  un tipo nuevo en el contrato.
- El cuerpo de `GET /salud` y el de los errores (`{"detail": "..."}`, el formato de FastAPI) tampoco
  están en el contrato. Son respuestas de servicio, no datos del análisis; `EstadoServicio` es solo
  `{"estado": "ok"}` y vive en la capa HTTP.

---

## Decisión 3: Reutilizar `pipeline.py` sin cambiarlo

**Elegido**: el servidor llama a `preparar_para_confirmar` (fase 1) y `analizar_confirmado` (fase 2)
con un `Pasos` hecho de los módulos reales: `audio.preparar`, `audio.diarizacion`,
`voz.clasificador`, `audio.fragmentos` y `analisis.analizar`. La función `notificar` guarda cada
`EstadoAnalisis` en el registro.

**Justificación**: el núcleo ya está probado. El servidor solo añade la capa HTTP, la cola y el
registro. Las pruebas de la API usan un `Pasos` falso, así que no necesitan modelos ni GPU.

---

## Decisión 4: Una cola de un solo trabajador

**Elegido**: un `ThreadPoolExecutor(max_workers=1)`. Un análisis nuevo queda «en cola» hasta que el
trabajador lo coge. La fase 2 (el análisis, que es rápido) usa la misma cola, así que el orden se
conserva.

**Justificación**: hay una sola GPU (V100S) y pyannote la ocupa entera. Mientras tanto la API sigue
respondiendo, porque el trabajo no corre en el hilo de las peticiones. Las pruebas inyectan un
ejecutor síncrono, que hace el trabajo en el momento.

**Alternativas descartadas**:
- `BackgroundTasks` de FastAPI: no limita cuántos análisis corren a la vez.
- Celery o Redis: demasiada infraestructura para el MVP.

---

## Decisión 5: Registro en memoria y ficheros en una carpeta de trabajo

**Elegido**: un registro en memoria (`dict` protegido con un `Lock`) con el estado de cada análisis.
El audio subido y su WAV van en `CARPETA_TRABAJO`. Por defecto es una subcarpeta del directorio
temporal del sistema, nunca el repositorio (RD-04).

**Justificación**: un solo proceso basta para el MVP y la demo. Si el servidor se reinicia, los
análisis en curso se pierden; la retención borra igualmente sus ficheros por fecha (decisión 9).

**Alternativas descartadas**:
- Una base de datos: no la pide el funcional y añade una pieza que mantener.

---

## Decisión 6: Seguridad de la subida (RNF-10)

**Elegido**, en este orden:

1. **Tamaño**: se rechaza con 413 si `Content-Length` pasa de 200 MB, antes de leer el cuerpo, y una
   petición sin `Content-Length` se rechaza con 411. Además, el fichero se copia a disco por trozos
   y se corta al pasar el límite, por si la cabecera miente. El multipart se lee con el parser de
   `python-multipart` directamente sobre el flujo de la petición, y el audio se escribe ya en
   `CARPETA_TRABAJO`: no se usa `request.form()` de Starlette, que deja una copia en el directorio
   temporal del sistema, fuera del alcance de la retención (T049–T050).
2. **Nombre**: el fichero se guarda como `<id>.subida`, con un `id` aleatorio (`uuid4`). El nombre
   original no se guarda, no se registra y no sale en ningún mensaje.
3. **Tipo real**: se leen los primeros bytes y se acepta solo WAV (`RIFF…WAVE`), MP3 (`ID3` o una
   cabecera de trama MPEG), OGG (`OggS`), FLAC (`fLaC`) y M4A (`ftyp` en el byte 4). La extensión y el
   tipo MIME no cuentan. Lo demás se rechaza con 415.
4. **Duración**: `ffprobe` mide la duración antes de crear el análisis, con argumentos en lista
   (`subprocess.run` sin shell), la ruta como `file:` y tiempo máximo. Más de 60 min, o un fichero que
   `ffprobe` no entiende, se rechaza con 422.
5. **Conversión**: `audio/preparar.py` ya llama a ffmpeg sin shell, con tiempo máximo y sin el nombre
   del fichero en los errores.

Si algo se rechaza, se borra el fichero y no se crea ningún análisis (spec, historia 1, escenario 2).

**Justificación**: es lo que piden RNF-10, FR-001 y FR-002. Los bytes mágicos no necesitan ninguna
dependencia, y `ffprobe` llega con ffmpeg, que ya se usa.

**Alternativas descartadas**:
- `python-magic`: depende de libmagic, que en Windows hay que instalar aparte.

---

## Decisión 7: Fragmentos recortados del WAV, sin ffmpeg

**Elegido**: `GET /analisis/{id}/fragmento?inicio=&fin=` lee con el módulo `wave` solo las muestras
del tramo pedido del WAV mono 16 kHz que deja `preparar` y devuelve un WAV nuevo (`audio/wav`). Se
rechaza con 422 si `inicio < 0`, si `fin <= inicio`, si `fin` pasa de la duración o si el tramo dura
más de `escucha_max_segundos` (15 s, 9.3).

**Justificación**: no lanza procesos, no guarda fragmentos en disco (nada que borrar) y garantiza el
máximo de 15 s (SC-007). La web pide el margen de RF-18 (1 s antes) recortado a 15 s.

---

## Decisión 8: Modo manual por análisis

**Elegido**: `POST /analisis` recibe el campo de formulario `modo_manual` (por defecto, falso) y se lo
pasa a `preparar_para_confirmar`, que con él no llama a `proponer_voz` (RF-08). Una prueba usa un
`proponer_voz` falso que falla si alguien lo llama.

**Justificación**: la spec 001 aclaró que el modo manual es una opción por análisis. Tiene que
elegirse antes de subir, porque el clasificador corre en la fase 1.

---

## Decisión 9: Retención de 24 h [VALIDAR]

**Elegido**: una función `borrar_caducados(ahora)` borra el audio subido y el WAV de los análisis con
más de 24 h desde la subida. Se queda solo el `Resultado` (datos agregados y tiempos, sin audio).
Además borra de `CARPETA_TRABAJO` cualquier fichero de más de 24 h por su fecha, incluidos los que
dejó un servidor que se reinició. Un análisis caducado que no había terminado pasa a «error» con el
motivo «Se cumplió el plazo de retención». Después, `fragmento` y `hablantes` responden 410.

Un hilo la ejecuta cada 10 min mientras el servidor está en marcha. Las pruebas la llaman con un reloj
falso y revisan el disco (SC-006).

---

## Decisión 10: Demo pública sin subidas [VALIDAR]

**Elegido**: la variable de entorno `DEMO_PUBLICA` (por defecto, desactivada). Si está activa,
`POST /analisis` con audio responde 403 «La demo pública no admite subidas»; los ejemplos siguen
funcionando.

---

## Decisión 11: Ejemplos precalculados

**Elegido**: los ejemplos son `Resultado` en JSON dentro de la carpeta `EJEMPLOS_DIR`, por defecto
`backend/ejemplos/`. `GET /ejemplos` los lista; `POST /analisis` con el campo `ejemplo=<id>` crea un
análisis ya «terminado» con ese resultado (8.1: los ejemplos se saltan la confirmación). No se lee
nada de `tests/` en producción.

**Punto abierto para el equipo**: hoy los únicos ejemplos son los tres sintéticos de
`backend/tests/ejemplos`. Los reales se generan con `scripts/analizar_audio.py` sobre audios con
licencia (no sobre la partición de prueba, regla 9). Hasta tenerlos, se copian los sintéticos y la web
los presenta como sintéticos.

---

## Decisión 12: Cómo habla la web con el servidor

**Elegido**: `frontend/src/services/api.ts` llama a las rutas de verdad a través del proxy de Vite
(`/api` → `localhost:8000`, ya configurado), consulta el estado cada segundo hasta «esperando
confirmación» o «error» y pide los fragmentos a `GET /fragmento`. Se quita la simulación: si el
backend no responde, la web lo dice y solo ofrece lo que no lo necesita. Después, los tipos de
`types/contrato.ts` se generan desde `/openapi.json` con `openapi-typescript` (MIT; FR-015, RD-02).

**Fuera de este plan**: los fallos de las pantallas señalados en la revisión (confirmación rellenada
de antemano, reproductor, colores, etc.) y la página «Cómo funciona». Reintentar un análisis en
error (FR-004) tampoco entra: no hay ruta en 9.3, y una ruta que no está en 9.3 no existe.
