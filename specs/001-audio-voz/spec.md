# Especificación de la feature: Audio y voz

**Rama de trabajo**: `feat/moni/fase1` (creación de la spec; la implementación irá en la rama de la persona A)

**Creada**: 2026-10-24

**Estado**: Borrador

**Responsable**: Persona A (audio y voz)

**Entrada**: «Audio y voz: normalizar el audio a WAV mono de 16 kHz, separar hablantes y solapamientos con pyannote, proponer voz femenina, masculina o no determinada con inaSpeechSegmenter, modo manual sin propuesta y fragmentos para confirmar cada voz (RF-03, RF-05, RF-06, RF-08 y fragmentos de RF-07; M-02 y M-03). Fuente de verdad: docs/01-funcional.md.»

**Fuente de verdad**: [docs/01-funcional.md](../../docs/01-funcional.md). Si esta spec y el funcional no coinciden, manda el funcional (constitución, punto 1).

## Clarifications

### Session 2026-10-24

- Q: ¿Con qué criterio selecciona el sistema los ≥ 3 fragmentos de un hablante? → A: Distribuidos uniformemente a lo largo del audio del hablante (inicio, mitad, final y los que hagan falta).
- Q: ¿El «modo manual» es una opción por análisis o una configuración global? → A: Opción por análisis; cada análisis lleva su propio campo `modo` (asistido / manual).
- Q: Cuando falla un paso del pipeline, ¿el sistema se detiene de inmediato o continúa? → A: Parada inmediata; el primer paso fallido detiene el análisis y lo marca como «error» con el motivo.
- Q: ¿Los ≥ 3 fragmentos de un hablante deben ser estrictamente no solapados entre sí? → A: Sí, cada fragmento abarca segundos distintos; ninguno comparte tiempo con otro del mismo hablante.
- Q: ¿Hay una duración mínima para registrar un solapamiento entre hablantes? → A: No; la diarización devuelve todos los solapamientos detectados por pyannote, sin filtrar por duración. El filtro de > 0,3 s lo aplica la persona B en su regla de interrupciones (`solapamiento_mas_de` en config.py).

## Escenarios de uso y pruebas *(obligatorio)*

### Historia 1 - Preparar el audio y separar las voces (Prioridad: P1)

Una analista sube un audio. El sistema lo convierte a un formato único y averigua cuántas voces hay, cuándo habla cada una y cuándo hablan dos a la vez, sin saber quién es nadie.

**Por qué esta prioridad**: sin turnos y solapamientos no hay ninguna métrica (OE1 a OE3). Es el primer paso del recorrido mínimo (plan, Parte 0, prioridad 1).

**Prueba independiente**: se pasa un fragmento de 5 min de la reunión de desarrollo IB4002 y se comprueba que salen turnos por «Hablante n» y solapamientos con el formato del contrato de datos.

**Escenarios de aceptación**:

1. **Dado** un audio válido en mp3, wav, m4a, ogg o flac, **cuando** se prepara, **entonces** sale un audio mono de 16 kHz cuya duración coincide con la de entrada ± 0,1 s (RF-03).
2. **Dado** el audio preparado, **cuando** se separan las voces, **entonces** se devuelven los turnos de cada «Hablante n» y los tramos en que dos o más hablantes se solapan, con el formato del contrato (RF-05).
3. **Dado** que falla la preparación o la separación, **cuando** termina el paso, **entonces** el análisis queda en «error» con su motivo, nunca colgado (RNF-16).

---

### Historia 2 - Proponer cómo suena cada voz (Prioridad: P1)

Para cada hablante, el sistema propone una etiqueta para su voz (femenino, masculino o indeterminado), con una confianza entre 0 y 1. Es solo una propuesta: la decide una persona (RN-02).

**Por qué esta prioridad**: es Must en modo asistido, el modo del MVP (D-04), y lo necesita la pantalla Confirmar voces.

**Prueba independiente**: se pasa un audio con hablantes cuyo sexo de referencia se conoce (código F o M de AMI) y se comprueba que cada uno recibe una propuesta con su confianza.

**Escenarios de aceptación**:

1. **Dado** un hablante separado, **cuando** se calcula la propuesta, **entonces** tiene una etiqueta (femenino, masculino o indeterminado) y una probabilidad entre 0 y 1 (RF-06).
2. **Dado** un hablante cuya probabilidad cae en la zona dudosa (0,35–0,65 [VALIDAR]), **cuando** se calcula la propuesta, **entonces** la propuesta es «indeterminado» (RF-06).
3. **Dada** una propuesta, **cuando** se guarda, **entonces** consta que la etiqueta viene del modelo y no de una persona (RF-07).

---

### Historia 3 - Dar fragmentos para confirmar cada voz (Prioridad: P1)

Para que una persona confirme o corrija la propuesta escuchando, el sistema elige y corta fragmentos cortos de cada hablante, distribuidos uniformemente a lo largo del audio del hablante (inicio, mitad, final y los que hagan falta).

**Por qué esta prioridad**: sin fragmentos no se puede confirmar, y sin confirmación no hay resultados (RF-07, RN-02).

**Prueba independiente**: con un audio separado, se comprueba que cada hablante presente tiene al menos 3 fragmentos de entre 3 y 5 s que solo contienen su voz.

**Escenarios de aceptación**:

1. **Dado** un hablante presente (10 s o más de habla y 3 tramos de 3 s o más sin solapamiento, RN-01 [VALIDAR]), **cuando** se generan los fragmentos, **entonces** hay al menos 3, cada uno de 3 a 5 s (RF-07).
2. **Dado** un hablante con 10 s o más de habla que no tiene 3 tramos de 3 s o más sin solapamiento, **cuando** se generan los fragmentos, **entonces** no es una voz presente: no pasa a confirmación y su tiempo se muestra aparte como voz corta (D-18).

---

### Historia 4 - Modo manual, sin propuesta automática (Prioridad: P2)

Una analista elige el modo manual: ningún modelo infiere cómo suena la voz y la persona etiqueta después de escuchar.

**Por qué esta prioridad**: es Should (RF-08), pero es la base del apartado ético (sección 4.3) y el plan prohíbe recortarlo (Parte 15).

**Prueba independiente**: con el modo manual activo, se comprueba que el clasificador de voz no se ejecuta y que los hablantes llegan a confirmación sin propuesta.

**Escenarios de aceptación**:

1. **Dado** el modo manual activo, **cuando** se analiza un audio, **entonces** no se ejecuta ningún clasificador de voz (RF-08).
2. **Dado** el modo manual activo, **cuando** llegan los hablantes a confirmación, **entonces** tienen fragmentos pero ninguna propuesta previa (RF-08).

---

### Casos límite

- **Hablante con menos de 10 s de habla:** no cuenta como presente (RN-01): no recibe propuesta ni fragmentos y no pasa a confirmación, pero su tiempo se muestra aparte en el resultado (D-15).
- **Audio sin ninguna voz presente** o con una sola: el análisis queda en «error» con un motivo claro («solo se ha detectado una voz que se pueda confirmar»), porque con una sola voz no hay nada que comparar (D-17, RNF-16).
- **Audio largo en CPU:** en desarrollo se trabaja con fragmentos de 5 min; los audios completos van a GPU (plan, Parte 5.2).
- **Hablante con poco audio:** no es una voz presente (D-18): no aparece en Confirmar voces y su tiempo se muestra aparte.

## Requisitos *(obligatorio)*

### Requisitos funcionales

- **FR-001**: El sistema DEBE convertir el audio de entrada a mono de 16 kHz conservando la duración ± 0,1 s (RF-03, Must).
- **FR-002**: El sistema DEBE devolver los turnos de cada hablante, numerado como «Hablante n», y los tramos de habla simultánea, con el formato del contrato de datos (RF-05, Must; RN-10).
- **FR-003**: El sistema DEBE proponer para cada hablante una etiqueta (femenino, masculino o indeterminado), con una probabilidad entre 0 y 1 (RF-06, Must en modo asistido).
- **FR-004**: El sistema DEBE proponer «indeterminado» cuando la probabilidad cae en la zona dudosa, 0,35–0,65 [VALIDAR] (RF-06).
- **FR-005**: El sistema DEBE registrar que una propuesta viene del modelo (RF-07).
- **FR-006**: El sistema DEBE ofrecer al menos 3 fragmentos de 3 a 5 s por cada hablante presente, distribuidos uniformemente a lo largo del audio del hablante (inicio, mitad, final) y sin solapamiento entre sí (ningún segundo compartido) (RF-07).
- **FR-007**: Con el modo manual activo en un análisis concreto, el sistema NO DEBE ejecutar ningún clasificador de voz para ese análisis (RF-08, Should). El modo (asistido / manual) se especifica por análisis.
- **FR-008**: Si falla cualquier paso del pipeline, el sistema DEBE detenerse de inmediato, sin ejecutar pasos posteriores, y marcar el análisis como «error» con el motivo del fallo (RNF-16, Must).
- **FR-009**: El sistema NO DEBE identificar a nadie ni guardar ninguna huella de voz; solo numera las voces dentro de cada audio (secciones 4.3 y 10.3; plan, Parte 2.2).
- **FR-010**: El audio DEBE procesarse en infraestructura propia, sin enviarse fuera (RNF-12, Must).
- **FR-011**: El sistema DEBE funcionar sin GPU, en CPU (RNF-20, Must).
- **FR-012**: Los umbrales (zona dudosa, presencia) DEBEN estar en un solo sitio de configuración y ajustarse solo con la partición de desarrollo (RD-05; plan, Parte 4).

### Entidades clave

Los nombres de campo definitivos los fija el contrato de datos (`docs/contrato_de_datos.md`), todavía pendiente.

- **Audio preparado**: el audio de entrada convertido a mono de 16 kHz, con su duración.
- **Análisis**: la unidad de procesamiento de un audio; lleva su propio campo `modo` (asistido o manual).
- **Hablante**: una voz distinta dentro de un audio, numerada «Hablante n»; no identifica a nadie.
- **Turno**: un tramo continuo en el que habla un hablante: hablante, inicio y fin en segundos con decimales.
- **Solapamiento**: un tramo en el que hablan dos o más hablantes a la vez: hablantes, inicio y fin. Se devuelven todos los detectados, sin filtrar por duración.
- **Propuesta de voz**: para un hablante, la etiqueta (femenino, masculino o indeterminado), la probabilidad y el origen (modelo).
- **Fragmento**: un tramo de 3 a 5 s de un hablante, con inicio y fin, para escucharlo al confirmar.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: En todos los audios de prueba, la duración del audio preparado coincide con la original ± 0,1 s (RF-03).
- **SC-002**: La tasa de error de diarización en la partición de prueba es del 20 % o menos [VALIDAR], y se publica con su intervalo de confianza del 95 % y su n (M-01, RNF-04, Should).
- **SC-003**: La exactitud equilibrada de la propuesta de voz, por hablante, es de 0,90 o más [VALIDAR] en la partición de prueba; se publica siempre, con IC 95 % y n, y se compara con la línea base del tono medio (M-02, RNF-03: Must publicarla, Should el umbral).
- **SC-004**: La diferencia de error de la propuesta de voz entre grupos es de 5 puntos porcentuales o menos [VALIDAR], y se publica siempre con su intervalo (M-03, RNF-06: Must publicarla).
- **SC-005**: Con el modo manual activo, el clasificador de voz se ejecuta 0 veces (RF-08).
- **SC-006**: El 100 % de los hablantes presentes llegan a confirmación con al menos 3 fragmentos de 3 a 5 s (RF-07).
- **SC-007**: Un episodio de 60 min se procesa en GPU en 15 min o menos [VALIDAR el domingo 25], mediana de 3 audios (RNF-01, Should).

## Supuestos

- **Motores decididos:** la separación de voces usa pyannote (`speaker-diarization-community-1`) en local y la propuesta de voz usa inaSpeechSegmenter preentrenado, sin entrenar ningún modelo (D-03). El plan B y la línea base es el tono medio de la voz con un umbral (plan, Parte 9 y tarea A11).
- **Modo por defecto:** en el MVP, modo asistido con confirmación humana siempre (D-04).
- **Datos:** desarrollo con las reuniones IB4002 e IB4010 de AMI; prueba con EN2002a, EN2002c, ES2004a, IS1009a, TS3003a y las grabaciones del equipo, solo para medir (sección 11.3; constitución, punto 9).
- **Referencia de voz:** en AMI, el sexo que el corpus registra en el código de cada participante (F o M); en las grabaciones, la autopresentación pública (sección 11.2).
- **Contrato:** esta spec depende de `docs/contrato_de_datos.md`, que todavía no existe. Las entidades de arriba se ajustarán a él.
- **Fuera de esta feature:** la subida y la validación del archivo (RF-01), la pantalla de confirmación (RF-07, persona C) y el cálculo de métricas (persona B).
