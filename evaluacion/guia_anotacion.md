# Guía de anotación de interrupciones

Para las dos personas que anotan (A y C). Moni no anota la prueba, porque diseña las reglas
(funcional, 11.2).

## 1. Para qué sirve

Vais a marcar, escuchando, las veces que una persona empieza a hablar mientras otra habla. Vuestras
marcas son la referencia con la que se mide:

- si el sistema detecta bien las interrupciones (M-05);
- si vosotras dos anotáis lo mismo (M-08, kappa de Cohen).

Por eso **anotad cada una por separado y no comentéis nada hasta que las dos hayáis terminado**.

## 2. Qué audios anotáis

- Las 2 grabaciones propias (de 3 a 5 minutos cada una).
- 5 minutos de la reunión EN2002a de AMI [COMPLETAR: propuesta, del minuto 0 al 5].

Las dos anotáis los mismos clips.

## 3. Palabras que usamos

- **Turno:** un tramo seguido en el que una persona habla.
- **Solapamiento:** un momento en el que dos personas hablan a la vez.
- **A** es la persona que ya estaba hablando. **B** es la que empieza a hablar mientras A habla.

## 4. Cuándo hay que anotar

Solo cuando **B empieza a hablar mientras A habla y las dos se pisan más de 0,3 segundos**. Si se pisan
0,3 segundos o menos, no se anota.

## 5. Los cuatro tipos

Anotad los cuatro. La evaluación decide después cuáles cuentan como interrupción.

| Tipo (escribid exactamente esto) | Cuándo | ¿Cuenta como interrupción? |
| --- | --- | --- |
| `con_exito` | A deja de hablar en los 2 segundos siguientes a que B empieza | Sí |
| `intento` | A sigue hablando y B habla 1 segundo o más | Sí |
| `senal_de_escucha` | B habla menos de 1 segundo y A sigue (un «ajá», un «claro») | No |
| `colaborativo` | Se solapan para acompañar y no para quitar la palabra: reír a la vez o completar la frase de la otra persona | No |

**Ejemplos**

- A habla del segundo 10 al 20. B empieza en el segundo 18 y A se calla en el 19,5. A se calló en
  1,5 segundos: `con_exito`.
- A habla del segundo 10 al 40. B empieza en el 18 y habla hasta el 30. A siguió hablando y B habló
  12 segundos: `intento`.
- A habla del segundo 10 al 40. B dice «ajá» entre el 18 y el 18,6. B habló menos de 1 segundo:
  `senal_de_escucha`.
- A cuenta una anécdota y B termina su frase a la vez que ella, entre risas, sin que A pierda la
  palabra: `colaborativo`.
- A habla del segundo 10 al 20. B empieza en el 19,8. Se pisan 0,2 segundos: no se anota nada.

**Si dudáis**, usad las reglas de tiempo (los tres primeros tipos). Poned `colaborativo` solo cuando
estéis seguras de que no se quita la palabra.

No hace falta medir al milisegundo: la evaluación admite 1 segundo de diferencia.

## 6. Cómo anotar en Audacity

Los nombres de los menús pueden cambiar un poco según la versión.

1. Abrid el audio.
2. Pistas → Añadir nueva → Pista de etiquetas.
3. Seleccionad con el ratón el tramo del solapamiento, **desde que B empieza hasta que se acaba el
   solapamiento**.
4. Pulsad **Ctrl+B** para añadir la etiqueta y escribid el tipo: `con_exito`, `intento`,
   `senal_de_escucha` o `colaborativo`.
5. Al terminar: Archivo → Exportar → Exportar etiquetas.

## 7. Dónde se guarda

En `evaluacion/etiquetas/`, con el nombre `<audio>_A.txt` o `<audio>_C.txt` (la A o la C es vuestra
persona del proyecto).

- Sin nombres de personas.
- El audio **nunca** se sube al repositorio (RD-04). Solo suben los ficheros de etiquetas.

## 8. Después de anotar

1. Comparáis vuestras dos anotaciones.
2. Los desacuerdos se resuelven hablando; el resultado es la referencia y se anota cuáles eran.
3. Moni calcula la kappa. Si sale menos de 0,6 [VALIDAR], se revisa esta guía y se vuelve a anotar
   (funcional, 11.2).

## 9. El límite que ya conocemos

El sistema no oye las palabras, así que no distingue las risas compartidas. Por eso existe
`colaborativo`: para que ese límite se vea en los resultados (D-16).
