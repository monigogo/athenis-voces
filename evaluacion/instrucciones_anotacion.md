# Cómo anotar las interrupciones

Resumen de una página de la [guía de anotación](guia_anotacion.md), que tiene los ejemplos completos.

Cada una anota **por separado** y **sin comentar nada** hasta que las dos terminéis.
Vani es **A** y Aroa es **C**. Moni no anota.

## 1. Qué audios

| Audio | Qué es | Hasta dónde |
| --- | --- | --- |
| `conversacion1` | Grabación propia, 3 voces | Todo el audio |
| `conversacion2` | Grabación propia, 3 voces | Todo el audio |
| `EN2002a` | Reunión de AMI (en `datos/ami/audios/`) | Solo hasta el minuto 5:00. **No cortéis el audio**, ábrelo entero |

## 2. Cuándo marcar

Solo cuando **B empieza a hablar mientras A ya habla** y se pisan **más de 0,3 segundos**.
Si se pisan menos, no se marca nada.

## 3. Qué nombre poner

Escribidlo exactamente así, sin tildes.

| Pasa esto | Poned |
| --- | --- |
| A se calla en los 2 segundos siguientes | `con_exito` |
| A sigue hablando y B habla 1 segundo o más | `intento` |
| B dice algo corto («ajá», «sí») y A sigue | `senal_de_escucha` |
| Se pisan para acompañar: reír a la vez o terminar la frase de la otra | `colaborativo` |

Si dudáis, elegid entre los tres primeros. Poned `colaborativo` solo si estáis seguras de que
nadie quita la palabra.

## 4. Cómo marcar en Audacity

| Paso | Qué hacer |
| --- | --- |
| 1 | Abrid el audio |
| 2 | Pistas → Añadir nueva → **Pista de etiquetas** |
| 3 | Con el ratón, seleccionad el trozo en que se pisan: desde que B empieza hasta que acaba el solapamiento |
| 4 | Pulsad **Ctrl+B** y escribid el nombre de la tabla de arriba |
| 5 | Al terminar: Archivo → Exportar → **Exportar etiquetas** |

## 5. Cómo llamar a los archivos

| Audio | Vani (A) | Aroa (C) |
| --- | --- | --- |
| `conversacion1` | `conversacion1_A.txt` | `conversacion1_C.txt` |
| `conversacion2` | `conversacion2_A.txt` | `conversacion2_C.txt` |
| `EN2002a` | `EN2002a_A.txt` | `EN2002a_C.txt` |

## 6. Qué subís

- Solo los archivos `.txt`.
- **Nunca el audio** (RD-04).
- **Sin nombres de personas** en ningún sitio.

## 7. Cuando terminéis las dos

1. Comparad vuestras anotaciones y hablad de los desacuerdos.
2. Guardad el resultado final de cada audio como `<audio>_referencia.txt`, con el mismo formato.
   Por ejemplo, `conversacion1_referencia.txt`.
3. Los archivos van a `evaluacion/etiquetas/`.
