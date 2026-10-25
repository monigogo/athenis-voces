# Contrato de datos

Versión del contrato: **0.2**

Qué datos se pasan el backend, la API y la web, campo por campo. El código que manda es
[`backend/src/contrato.py`](../backend/src/contrato.py): este documento lo explica en palabras.

Cambiar el contrato exige el acuerdo de las tres (constitución, regla 3): se cambian a la vez
`contrato.py`, este documento, los ejemplos y `VERSION_CONTRATO`.

## Reglas para todos los mensajes

- **Nombres** en español y sin tildes (funcional, 9.4).
- **Tiempos** en segundos con decimales, desde el principio del audio.
- **Hablantes** numerados desde 1. En pantalla se muestran como «Hablante n» y nunca con su nombre
  (RN-10).
- **`null` significa «no aplicable»**, nunca 0 (RN-13). La web lo muestra como «no aplicable».
- **Campos desconocidos:** se rechazan. Un nombre mal escrito da error, no se ignora.
- **`version_contrato`:** la llevan los mensajes completos y tiene que ser `"0.2"`.

## Qué mensaje va en cada ruta de la API

| Ruta (funcional, 9.3) | Mensaje |
| --- | --- |
| `GET /analisis/{id}` | [EstadoAnalisis](#estadoanalisis) |
| `GET /analisis/{id}/hablantes` | [HablantesParaConfirmar](#hablantesparaconfirmar) |
| `POST /analisis/{id}/confirmacion` | Recibe [Confirmacion](#confirmacion) |
| `GET /analisis/{id}/resultado` | [Resultado](#resultado) |

[EntradaAnalisis](#entradaanalisis) no sale por la API: es lo que el pipeline le pasa al análisis.

## Ejemplos

Tres resultados completos y válidos, para trabajar sin audio (por ejemplo, la web en modo falso):

- [`backend/tests/ejemplos/con_voces_femeninas.json`](../backend/tests/ejemplos/con_voces_femeninas.json)
- [`backend/tests/ejemplos/sin_voces_femeninas.json`](../backend/tests/ejemplos/sin_voces_femeninas.json):
  los índices salen «no aplicable».
- [`backend/tests/ejemplos/muchas_interrupciones.json`](../backend/tests/ejemplos/muchas_interrupciones.json)

## Valores fijos

### EtiquetaVoz

Cómo suena una voz. Las tres opciones de la pantalla Confirmar voces (constitución, regla 8).

| Valor | Qué es |
| --- | --- |
| `femenino` | Voz femenina |
| `masculino` | Voz masculina |
| `indeterminado` | No se puede decir. Su tiempo nunca se reparte entre las otras dos (RN-03) |

### OrigenEtiqueta

Quién fijó la etiqueta final (RF-07).

| Valor | Qué es |
| --- | --- |
| `modelo` | La propuesta del modelo, aceptada |
| `persona` | La eligió o la corrigió una persona |

### Estado

En qué punto está un análisis (RF-04).

| Valor | Qué es |
| --- | --- |
| `en_cola` | Subido, esperando turno |
| `procesando` | Separando voces o calculando; lleva `progreso` |
| `esperando_confirmacion` | Falta que una persona confirme las voces |
| `terminado` | El resultado está listo |
| `error` | Algo falló; lleva `motivo_error` |

### TipoSolapamiento

Qué pasa cuando alguien empieza a hablar mientras otra persona habla, y se pisan más de 0,3 s
(funcional, 6.7).

| Valor | Qué es | ¿Es interrupción? |
| --- | --- | --- |
| `con_exito` | Quien hablaba se calla en los 2 s siguientes | Sí |
| `intento` | Quien hablaba sigue, y quien entra habla 1 s o más | Sí |
| `senal_de_escucha` | Quien entra habla menos de 1 s («ajá», «sí») | No (RN-07) |

### NombreIndice

Los índices de grupo (RF-16).

| Valor | Qué es |
| --- | --- |
| `ratio_representacion` | Ratio de representación (RR): 1 si las voces femeninas hablan lo proporcional a cuántas son; menos de 1, hablan menos |
| `brecha_interrupcion` | Brecha de interrupción (BI): más de 1, se interrumpe más a las voces femeninas, ya corregido por cuánto habla cada grupo |

## Tiempos

### Tramo

Un trozo del audio. Es la base de los cuatro tipos siguientes. `fin` siempre es mayor que `inicio`.

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `inicio` | segundos | Dónde empieza |
| `fin` | segundos | Dónde acaba |

### Turno

Un tramo en el que habla una sola persona (RF-05). Tiene los campos de [Tramo](#tramo) y además:

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `inicio` | segundos | Dónde empieza |
| `fin` | segundos | Dónde acaba |
| `hablante` | número desde 1 | Quién habla |

### Solapamiento

Un tramo en el que hablan dos o más personas a la vez (RF-05).

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `inicio` | segundos | Dónde empieza |
| `fin` | segundos | Dónde acaba |
| `hablantes` | lista de números, 2 o más, sin repetir | Quiénes hablan a la vez |

### Fragmento

Un trozo de 3 a 5 s de la voz de una persona, para escucharla al confirmar (RF-07).

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `inicio` | segundos | Dónde empieza |
| `fin` | segundos | Dónde acaba |

## Voz: propuesta y confirmación

### PropuestaVoz

Lo que propone el modelo para una persona. Solo propone: decide una persona (RN-02).

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `etiqueta` | [EtiquetaVoz](#etiquetavoz) | La voz que propone |
| `confianza` | de 0 a 1 | Cuánto confía. Entre 0,35 y 0,65 es una propuesta dudosa (RF-06) |

### Hablante

Una persona tal como aparece en la pantalla Confirmar voces. Solo llegan las voces presentes (RN-01).

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `hablante` | número desde 1 | Su número |
| `segundos_habla` | segundos | Cuánto habla en total |
| `propuesta` | [PropuestaVoz](#propuestavoz) o `null` | La propuesta del modelo; `null` en modo manual (RF-08) |
| `fragmentos` | lista de [Fragmento](#fragmento) | Al menos 3, para escucharla (RF-07) |

### HablantesParaConfirmar

Respuesta de `GET /analisis/{id}/hablantes`.

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `version_contrato` | texto | `"0.2"` |
| `id_analisis` | texto | El análisis |
| `hablantes` | lista de [Hablante](#hablante), sin repetir | Las voces que hay que confirmar |

### EtiquetaConfirmada

La etiqueta final de una persona.

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `hablante` | número desde 1 | Su número |
| `etiqueta` | [EtiquetaVoz](#etiquetavoz) | La voz confirmada |
| `origen` | [OrigenEtiqueta](#origenetiqueta) | Si se aceptó la propuesta o la eligió una persona |

### Confirmacion

Lo que manda la web en `POST /analisis/{id}/confirmacion`. Tiene que traer justo las voces de
[HablantesParaConfirmar](#hablantesparaconfirmar), ni una más ni una menos.

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `version_contrato` | texto | `"0.2"` |
| `etiquetas` | lista de [EtiquetaConfirmada](#etiquetaconfirmada), al menos 1, sin repetir hablante | Una por voz |

## Estado

### EstadoAnalisis

Respuesta de `GET /analisis/{id}`.

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `version_contrato` | texto | `"0.2"` |
| `id_analisis` | texto | El análisis |
| `estado` | [Estado](#estado) | En qué punto está |
| `progreso` | de 0 a 100 o `null` | Solo, y siempre, en `procesando` |
| `motivo_error` | texto o `null` | Solo, y siempre, en `error`. Por ejemplo: «Solo se ha detectado una voz que se pueda confirmar; hacen falta al menos 2» (D-17) |

## Entrada del análisis

### EntradaAnalisis

Lo que recibe el análisis tras la confirmación. No sale por la API.

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `version_contrato` | texto | `"0.2"` |
| `duracion` | segundos, más de 0 | Lo que dura el audio |
| `turnos` | lista de [Turno](#turno) | Todos, también los de las voces cortas |
| `solapamientos` | lista de [Solapamiento](#solapamiento) | Todos, sin filtrar por duración |
| `etiquetas` | lista de [EtiquetaConfirmada](#etiquetaconfirmada) | Las voces confirmadas; las que no están son voces cortas (D-15) |

## Resultado

### Interrupcion

Un solapamiento entre dos personas, ya clasificado (RF-14). Incluye las señales de escucha, que no
cuentan como interrupción.

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `inicio` | segundos | Dónde empieza |
| `fin` | segundos | Dónde acaba |
| `interrumpe` | número desde 1 | Quién entra |
| `interrumpido` | número desde 1, distinto | Quién estaba hablando |
| `tipo` | [TipoSolapamiento](#tiposolapamiento) | Qué tipo es |

### MetricasHablante

Las cifras de una persona (funcional, 6.7).

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `hablante` | número desde 1 | Su número |
| `etiqueta` | [EtiquetaVoz](#etiquetavoz) | Su voz confirmada |
| `origen` | [OrigenEtiqueta](#origenetiqueta) | Quién fijó la etiqueta |
| `segundos_habla` | segundos | Cuánto habla |
| `turnos` | recuento | Sus turnos; las señales de escucha no cuentan (D-14) |
| `turnos_largos` | recuento | Turnos de más de 30 s (MD-06) |
| `abre` | sí / no | Tiene el primer turno de más de 5 s (MD-07) |
| `cierra` | sí / no | Tiene el último turno de más de 5 s (MD-08) |
| `interrupciones_recibidas` | recuento | Le interrumpen, con éxito o en intento (MD-14) |
| `interrupciones_hechas` | recuento | Interrumpe, con éxito o en intento (MD-14) |
| `tasa_interrupcion_recibida` | por cada 10 min de habla, o `null` | Interrupciones recibidas por cada 600 s de habla propia (MD-15, RN-08) |
| `recupera_palabra` | de 0 a 100 o `null` | % de interrupciones con éxito tras las que vuelve a hablar en 10 s o menos (MD-16) |
| `apoyos_recibidos` | por cada 10 min de habla, o `null` | Señales de escucha que recibe mientras habla (MD-17) |
| `indice_protagonismo` | de 0 a 100 o `null` | Índice de protagonismo (RF-16, Should) |

### MetricasGrupo

Las cifras de un grupo de voces (funcional, 6.7).

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `etiqueta` | [EtiquetaVoz](#etiquetavoz) | El grupo |
| `numero_voces` | recuento | Cuántas voces tiene (MD-02) |
| `segundos_habla` | segundos | Cuánto habla el grupo |
| `cuota_tiempo` | de 0 a 100 o `null` | % del tiempo de las voces etiquetadas (MD-04, RN-04) |
| `turnos` | recuento | Turnos del grupo |
| `cuota_turnos` | de 0 a 100 o `null` | % de los turnos (MD-05) |
| `interrupciones_recibidas` | recuento | Interrupciones que recibe el grupo |
| `tasa_interrupcion_recibida` | por cada 10 min de habla, o `null` | La que usa la brecha de interrupción |

### Indice

Un índice de grupo con su fórmula, para que se pueda explicar (RN-06).

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `nombre` | [NombreIndice](#nombreindice) | Qué índice es |
| `valor` | 0 o más, o `null` | `null` = «no aplicable» (RN-13), por ejemplo si no hay voces femeninas |
| `formula` | texto | La fórmula, para mostrarla junto al valor |

### Resultado

Respuesta de `GET /analisis/{id}/resultado`.

| Campo | Tipo | Qué es |
| --- | --- | --- |
| `version_contrato` | texto | `"0.2"` |
| `id_analisis` | texto | El análisis |
| `duracion` | segundos, más de 0 | Lo que dura el audio |
| `voz_femenina_presente` | sí / no | Hay al menos una voz femenina (MD-01) |
| `primera_intervencion_femenina` | segundos o `null` | Cuándo habla por primera vez una voz femenina (MD-03) |
| `segundos_voces_cortas` | segundos | Tiempo de las voces que no son presentes; se muestra aparte y no cuenta como voz (D-15, D-18) |
| `grupos` | lista de [MetricasGrupo](#metricasgrupo), sin repetir | Un elemento por grupo |
| `hablantes` | lista de [MetricasHablante](#metricashablante), sin repetir | Una por voz presente |
| `turnos` | lista de [Turno](#turno) | Para la línea de tiempo |
| `solapamientos` | lista de [Solapamiento](#solapamiento) | Para la línea de tiempo |
| `interrupciones` | lista de [Interrupcion](#interrupcion) | Para la tabla con «escuchar» (RF-18) |
| `indices` | lista de [Indice](#indice), sin repetir | Los índices de grupo |
