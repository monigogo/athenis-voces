# Contrato HTTP: API interna (funcional, 9.3)

Rutas, entradas y salidas del servidor. Los cuerpos JSON son tipos de `backend/src/contrato.py`,
salvo `GET /salud` y los errores (research, decisión 2). La descripción OpenAPI que publica el
servidor en `/openapi.json` manda sobre este documento (RD-02): una ruta que no está en ella no existe.

Detrás del proxy de Vite, la web antepone `/api` a cada ruta.

---

## GET /salud

**200** `{"estado": "ok"}`. No mira los modelos: solo dice que el servicio responde.

## POST /analisis

`multipart/form-data`, con **una** de estas dos opciones:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `audio` | fichero | mp3, wav, m4a, ogg o flac; tipo real por contenido |
| `modo_manual` | `true`/`false` | Opcional, por defecto `false` (RF-08) |
| `ejemplo` | texto | `id_analisis` de un ejemplo de `GET /ejemplos` |

**201** `EstadoAnalisis`: con audio, `en_cola`; con ejemplo, `terminado`.
**400** si no llega ninguna de las dos opciones, o llegan las dos.
**403** con audio en la demo pública. **404** ejemplo desconocido. **411**, **413**, **415** y
**422**: ver las reglas de validación en [data-model.md](../data-model.md).

## GET /analisis/{id}

**200** `EstadoAnalisis`. **404** si no existe.

## GET /analisis/{id}/hablantes

**200** `HablantesParaConfirmar`, solo con las voces presentes. En modo manual, `propuesta` es `null`.
**409** si el estado no es `esperando_confirmacion`. **410** si ya se borró el audio.

## POST /analisis/{id}/confirmacion

Cuerpo `Confirmacion` (con `version_contrato`). **202** `EstadoAnalisis` (`procesando`; el análisis
corre en la cola).
**409** si el estado no es `esperando_confirmacion`. **422** si no confirma justo las voces
presentes o si el cuerpo no cumple el contrato.

## GET /analisis/{id}/resultado

**200** `Resultado`. **409** si el estado no es `terminado`.

## GET /analisis/{id}/fragmento?inicio=&fin=

**200** `audio/wav`, mono 16 kHz, con el tramo pedido. **422** si `inicio < 0`, si `fin <= inicio`,
si `fin` pasa de la duración o si el tramo dura más de 15 s. **409** si todavía no hay WAV.
**410** si ya se borró por la retención.

## GET /ejemplos

**200** `list[Resultado]`, ordenada por `id_analisis`.

## Errores

Cuerpo `{"detail": "<motivo en español>"}`. Nunca lleva el nombre del fichero subido, rutas del
servidor ni claves.
