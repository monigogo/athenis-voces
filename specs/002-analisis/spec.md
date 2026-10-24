# Especificación de la feature: Análisis y evaluación

**Rama de trabajo**: `feat/moni/fase1` (creación de la spec; la implementación irá en la rama de la persona B)

**Creada**: 2026-10-24

**Estado**: Borrador

**Responsable**: Persona B (Monica Gomez)

**Entrada**: «Análisis y evaluación: presencia, participación, quién abre y quién cierra, interrupciones por reglas de tiempo en tres tipos, ratio de representación, brecha de interrupción e índice de protagonismo, y evaluación del sistema (RF-12, RF-13 abre y cierra, RF-14, RF-16; M-01, M-04, M-05, M-08 y M-09).»

**Fuente de verdad**: [docs/01-funcional.md](../../docs/01-funcional.md), sobre todo el catálogo 6.7, las reglas de negocio 5.1 y la metodología 11. Si esta spec y el funcional no coinciden, manda el funcional (constitución, punto 1).

## Escenarios de uso y pruebas *(obligatorio)*

### Historia 1 - Presencia y participación (Prioridad: P1)

Con los turnos y las etiquetas de voz ya confirmadas, el sistema dice si hay voces femeninas, cuántas hay de cada grupo, cuándo habla la primera y qué parte del tiempo y de los turnos ocupa cada grupo.

**Por qué esta prioridad**: responde a la primera pregunta del proyecto (OE1) y es Must (RF-12).

**Prueba independiente**: con 3 casos sintéticos (turnos y etiquetas inventados) cuyo resultado se ha calculado a mano, se comprueba que todas las cifras coinciden.

**Escenarios de aceptación**:

1. **Dado** al menos un hablante etiquetado como femenino con 10 s o más de habla, **cuando** se calcula, **entonces** «voz femenina presente» vale sí (MD-01, RN-01 [VALIDAR]).
2. **Dados** los turnos etiquetados, **cuando** se calcula, **entonces** se obtienen las voces por grupo (MD-02), el inicio de la primera intervención femenina en min:s (MD-03), la cuota de tiempo (MD-04), la cuota de turnos (MD-05) y los turnos de más de 30 s de cada persona (MD-06).
3. **Dado** un hablante etiquetado como «indeterminado», **cuando** se calculan los porcentajes por grupo, **entonces** su tiempo no entra en el denominador, no se reparte entre los otros dos grupos y se informa aparte (RN-03, RN-04).

---

### Historia 2 - Quién abre y quién cierra (Prioridad: P1)

El sistema dice qué persona tiene el primer y el último turno de más de 5 s del episodio.

**Por qué esta prioridad**: es el ejemplo de protagonismo que dan las bases del reto («hablar al principio de un acto público, o cerrarlo») y es Must (RF-13, solo abre y cierra; «presenta» es Won't).

**Prueba independiente**: los mismos 3 casos sintéticos de la historia 1, con abre y cierra calculados a mano.

**Escenarios de aceptación**:

1. **Dado** un episodio cuyo primer turno dura 5 s o menos, **cuando** se calcula «abre», **entonces** se elige el primer turno de más de 5 s, no el primero (MD-07).
2. **Dado** un episodio, **cuando** se calcula «cierra», **entonces** se elige el último turno de más de 5 s (MD-08).

---

### Historia 3 - Detectar y clasificar interrupciones (Prioridad: P1)

El sistema encuentra los momentos en que una persona empieza a hablar mientras otra habla y los clasifica en tres tipos, mirando solo los tiempos y nunca lo que se dice.

**Por qué esta prioridad**: responde a la tercera pregunta del proyecto (OE3) y es Must (RF-14).

**Prueba independiente**: con un caso sintético de cada tipo, se comprueba que los tres se clasifican bien.

**Escenarios de aceptación**:

1. **Dado** un cambio de A a B en el que B empieza mientras A habla y se pisan 0,3 s o menos, **cuando** se analiza, **entonces** no es candidato (6.7).
2. **Dado** un candidato en el que A deja de hablar en los 2 s siguientes, **cuando** se clasifica, **entonces** es «con éxito» y cuenta como interrupción (6.7, RN-07).
3. **Dado** un candidato en el que A sigue hablando y B habla 1 s o más, **cuando** se clasifica, **entonces** es «intento» y cuenta como interrupción.
4. **Dado** un candidato en el que B habla menos de 1 s y A sigue, **cuando** se clasifica, **entonces** es «señal de escucha» y no cuenta como interrupción.
5. **Dadas** las interrupciones clasificadas, **cuando** se calcula, **entonces** se obtienen, por persona, las interrupciones recibidas y hechas (MD-14), la tasa recibida por cada 10 min de habla propia (MD-15, RN-08), el % de interrupciones con éxito tras las que vuelve a hablar en 10 s o menos (MD-16) y las señales de escucha que recibe por cada 10 min (MD-17).
6. **Dada** cualquier interrupción, **cuando** se muestra, **entonces** lleva su inicio y su fin para poder escucharla (RN-06, RF-18).

---

### Historia 4 - Ratio de representación y brecha de interrupción (Prioridad: P1)

El sistema resume el episodio en dos índices: si las voces femeninas hablan en proporción a cuántas son y si se las interrumpe más que a las masculinas, ya corregido por cuánto habla cada grupo.

**Por qué esta prioridad**: los dos primeros índices son Must (RF-16).

**Prueba independiente**: con casos sintéticos, se comprueba el valor de cada fórmula y que un grupo sin voces o sin tiempo da «no aplicable».

**Escenarios de aceptación**:

1. **Dados** los tiempos y recuentos por grupo, **cuando** se calcula, **entonces** RR = (T_F / T_E) ÷ (N_F / N_E) (6.7, RN-09).
2. **Dadas** las interrupciones recibidas y los tiempos por grupo, **cuando** se calcula, **entonces** BI = (I_F / (T_F / 600)) ÷ (I_M / (T_M / 600)).
3. **Dado** un episodio sin voces femeninas o sin voces masculinas (por ejemplo, IS1009a o TS3003a), **cuando** se calcula un índice cuyo denominador sería 0, **entonces** se muestran las tasas disponibles y el índice como «no aplicable», nunca un 0 ni un error (RN-13).
4. **Dado** cualquier índice, **cuando** se muestra, **entonces** lleva su fórmula (RN-06).

---

### Historia 5 - Índice de protagonismo (Prioridad: P3)

El sistema da a cada persona un índice de 0 a 100 que combina participación, posición y turnos largos.

**Por qué esta prioridad**: es Should (RF-16) y es lo primero que se recorta si falta tiempo (plan, Parte 15).

**Prueba independiente**: con un caso sintético, se comprueba la fórmula y que un componente cuyo máximo es 0 vale 0 para todas.

**Escenarios de aceptación**:

1. **Dada** una persona, **cuando** se calcula, **entonces** IP = 100 · (0,5 P + 0,25 O + 0,25 L), con P = su cuota de tiempo ÷ la de quien más habla, O = (abre + cierra) ÷ 2 y L = sus turnos de más de 30 s ÷ el máximo del episodio. Los pesos son [VALIDAR].
2. **Dado** un episodio sin turnos de más de 30 s, **cuando** se calcula, **entonces** L vale 0 para todas las personas.
3. **Dados** los pesos, **cuando** se varía cada uno ± 50 %, **entonces** se informa si cambia el orden de las personas (11.3).

---

### Historia 6 - Evaluar el sistema (Prioridad: P2)

El equipo mide cuánto acierta el sistema con audios reales, con líneas base, intervalos de confianza y sin tocar la partición de prueba al ajustar.

**Por qué esta prioridad**: es obligatorio para entregar (plan, Parte 0, prioridad 2) y pesa en calidad técnica, el 30 % (anexo B).

**Prueba independiente**: un solo script regenera las tablas de la sección 12.1 a partir de las etiquetas y las salidas guardadas, sin volver a procesar el audio.

**Escenarios de aceptación**:

1. **Dadas** las salidas guardadas y la referencia de AMI, **cuando** se evalúa la partición de prueba, **entonces** se obtienen el DER (M-01) y el error absoluto del % de tiempo femenino (M-04), cada uno con IC 95 % por bootstrap y su n.
2. **Dadas** las anotaciones de A y C, **cuando** se evalúa, **entonces** se obtienen la precisión, la exhaustividad y el F1 de las interrupciones con tolerancia de ± 1 s (M-05) y la kappa de Cohen entre anotadoras para el tipo de interrupción (M-08).
3. **Dada** la línea base «contar cualquier solapamiento como interrupción», **cuando** se evalúa, **entonces** se compara con las reglas.
4. **Dadas** las reglas, **cuando** se pasan sobre la separación de voces de referencia de AMI y sobre la de pyannote, **entonces** se informa la diferencia (ablación, 11.3).
5. **Dados** 3 audios completos procesados en GPU, **cuando** se cronometran, **entonces** se obtienen los minutos de proceso por hora de audio (M-09).

---

### Casos límite

- **Episodio sin voces femeninas** (TS3003a) o **sin masculinas** (IS1009a): RR o BI «no aplicable» (RN-13).
- **Solo voces «indeterminado»:** no hay voces etiquetadas; todas las cuotas e índices de grupo son «no aplicable» (RN-04, RN-13).
- **Persona sin tiempo de habla propio** para la tasa por 10 min: «no aplicable», nunca dividir por 0 (RN-13).
- **Habla simultánea:** el tiempo en que hablan dos o más a la vez cuenta entero para cada una (aclaración 1). La suma de los tiempos de habla puede superar la duración del episodio.
- **Discrepancia entre documentos:** el plan dice «no tiene voces o habla menos de 10 s» y el funcional (RN-13) dice «no tiene voces o tiempo». Manda el funcional; se anota para revisarlo en el anexo C.

## Requisitos *(obligatorio)*

### Requisitos funcionales

- **FR-001**: El sistema DEBE calcular MD-01 a MD-06 tal como los define el catálogo 6.7 (RF-12, Must). Las señales de escucha no cuentan como turno en la cuota de turnos (MD-05) ni en el recuento de turnos de cada persona (aclaración 2, D-14).
- **FR-002**: El sistema DEBE calcular por persona «abre» y «cierra» como el primer y el último turno de más de 5 s (RF-13, Must; MD-07 y MD-08).
- **FR-003**: El sistema DEBE marcar como candidato un cambio de A a B cuando B empieza mientras A habla y se pisan más de 0,3 s (RF-14, Must).
- **FR-004**: El sistema DEBE clasificar cada candidato como «con éxito», «intento» o «señal de escucha» según la tabla de 6.7. Los «2 s siguientes» de «con éxito» se cuentan desde que B empieza a hablar (aclaración 3).
- **FR-005**: Solo «con éxito» e «intento» DEBEN contar como interrupción (RN-07).
- **FR-006**: El sistema DEBE calcular MD-14 a MD-17, con las tasas por cada 10 min de habla de la persona interrumpida (RN-08).
- **FR-007**: El sistema DEBE calcular RR y BI con las fórmulas de 6.7 (RF-16, Must).
- **FR-008**: El sistema DEBERÍA calcular el índice de protagonismo con su análisis de sensibilidad (RF-16, Should).
- **FR-009**: Cualquier índice o tasa cuyo denominador sea 0 DEBE mostrarse como «no aplicable» (RN-13).
- **FR-010**: Las cuotas por grupo DEBEN calcularse sobre el tiempo de las voces femeninas y masculinas; el tiempo «indeterminado» se informa aparte y nunca se reparte (RN-03, RN-04).
- **FR-011**: Toda cifra DEBE llevar su fórmula, y toda interrupción, sus tiempos para escucharla (RN-06).
- **FR-012**: Los umbrales (10 s, 5 s, 30 s, 0,3 s, 2 s, 1 s, 10 s de recuperación) y los pesos DEBEN estar en un solo sitio de configuración y ajustarse solo con la partición de desarrollo (RD-05; plan, Parte 4).
- **FR-013**: Todo cambio de regla o de umbral DEBE anotarse en el anexo C con su motivo y su fecha (RD-06).
- **FR-014**: Si falla el cálculo, el análisis DEBE quedar en «error» con su motivo (RNF-16, Must).
- **FR-015**: La evaluación DEBE regenerar las tablas de 12.1 desde un único script, a partir de las etiquetas y las salidas guardadas (RNF-07, 11.4).
- **FR-016**: La evaluación DEBE usar la partición de prueba solo para medir, una vez por versión (RD-05; constitución, punto 9).
- **FR-017**: Toda comparación DEBE indicar el número de episodios y de minutos, y los resultados de un episodio no se generalizan (RN-12).
- **FR-018**: El resultado DEBE indicar aparte los segundos de las voces de menos de 10 s, que no cuentan como voz (RN-01, D-15).

### Entidades clave

Los nombres de campo definitivos los fija el contrato de datos (`docs/contrato_de_datos.md`), todavía pendiente.

- **Entrada del análisis**: los turnos y solapamientos de cada «Hablante n» (feature 001) y su etiqueta confirmada (femenino, masculino o indeterminado) con su origen (modelo o persona).
- **Métricas por persona**: tiempo, turnos, turnos largos, abre, cierra, interrupciones recibidas y hechas, tasas, recupera la palabra, apoyos e índice de protagonismo.
- **Métricas por grupo**: presencia, número de voces, primera intervención, cuotas de tiempo y de turnos.
- **Interrupción**: quién interrumpe, a quién, tipo, inicio y fin.
- **Índice**: nombre, valor o «no aplicable», fórmula y tasas de las que sale.
- **Resultado de evaluación**: métrica, partición, valor, IC 95 %, n y fecha.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: En 3 casos sintéticos, todas las métricas de presencia, participación y posición coinciden con el cálculo a mano (RF-12, RF-13).
- **SC-002**: Un caso sintético de cada tipo de interrupción se clasifica bien (RF-14).
- **SC-003**: Una prueba cubre la RN-13: con un grupo sin voces o sin tiempo, ningún índice da 0 ni falla (RF-16).
- **SC-004**: El F1 de las interrupciones con tolerancia de ± 1 s es de 0,70 o más [VALIDAR] en la partición de prueba, y se publica siempre con IC 95 % y n (M-05, RNF-05, Should).
- **SC-005**: El error absoluto del % de tiempo femenino se publica con IC 95 % y n (M-04).
- **SC-006**: La kappa entre anotadoras es de 0,6 o más [VALIDAR]; si no, se revisa la guía y se vuelve a anotar (M-08, 11.2).
- **SC-007**: La cobertura de pruebas del módulo de análisis es del 80 % de líneas o más [VALIDAR] (RNF-13, Should).
- **SC-008**: Una persona ajena al código regenera las tablas de 12.1 con un solo script (RNF-07, Must).

## Aclaraciones

### Sesión 2026-10-24

- **1. Tiempo durante un solapamiento:** cuenta entero para cada persona. Ejemplo: Ana habla de 0 a 10 s y Luis de 8 a 14 s; Ana suma 10 s y Luis 6 s.
- **2. Señales de escucha como turno:** no cuentan como turno. Sus segundos sí cuentan como tiempo de habla. Registrado como D-14.
- **3. Los 2 s de «con éxito»:** se cuentan desde que B empieza a hablar.

## Supuestos

- **Entradas confirmadas:** el análisis solo empieza cuando todas las voces presentes están confirmadas (RF-07, RN-02).
- **Grupos:** «voces etiquetadas» son las femeninas y las masculinas; «indeterminado» se informa aparte (RN-04).
- **Sin LLM y sin palabras:** todas las cifras las calcula el código a partir de tiempos (D-10). MD-09 a MD-13 están retiradas.
- **Límite declarado:** sin palabras, los solapamientos colaborativos pueden contarse como «intento»; cada caso se puede escuchar (6.7).
- **Datos:** desarrollo con IB4002 e IB4010; prueba con EN2002a, EN2002c, ES2004a, IS1009a, TS3003a y las grabaciones del equipo. La persona B no anota la prueba, porque diseña las reglas (11.2).
- **Referencia:** las anotaciones de AMI publicadas por BUT, y las anotaciones manuales de A y C para las interrupciones (plan, Parte 6).
- **Contrato:** depende de `docs/contrato_de_datos.md`, todavía pendiente.
- **Fuera de esta feature:** separar voces y proponer la voz (001), y mostrar los resultados en la web (003).
