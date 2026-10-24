# Especificación de la feature: Producto

**Rama de trabajo**: `feat/moni/fase1` (creación de la spec; la implementación irá en la rama de la persona C)

**Creada**: 2026-10-24

**Estado**: Borrador

**Responsable**: Persona C (producto)

**Entrada**: «Producto: API y web para subir un audio, seguir su estado, confirmar las voces, ver resultados con línea de tiempo e interrupciones que se pueden escuchar, ejemplos precalculados, página «Cómo funciona» y borrado al cumplir la retención (RF-01, RF-02, RF-04, RF-07 pantalla, RF-17, RF-18, RF-22, RF-23).»

**Fuente de verdad**: [docs/01-funcional.md](../../docs/01-funcional.md), sobre todo las secciones 8 (diseño funcional y UX) y 9.3 (API interna). Si esta spec y el funcional no coinciden, manda el funcional (constitución, punto 1).

## Escenarios de uso y pruebas *(obligatorio)*

### Historia 1 - Subir un audio y seguir su análisis (Prioridad: P1)

Una analista sube un audio desde la pantalla Analizar y ve en qué punto está el análisis.

**Por qué esta prioridad**: es la entrada del recorrido mínimo (plan, Parte 0) y es Must (RF-01, RF-04).

**Prueba independiente**: se sube un audio válido y uno que no es audio pero tiene extensión de audio; el primero crea un análisis «en cola» y el segundo se rechaza con su motivo.

**Escenarios de aceptación**:

1. **Dado** un archivo mp3, wav, m4a, ogg o flac dentro de los límites [NEEDS CLARIFICATION: tamaño y duración máximos; el funcional los deja como COMPLETAR en RF-01], **cuando** se sube, **entonces** se crea un análisis «en cola» (RF-01).
2. **Dado** un archivo que no es audio, comprobado por su contenido y no por la extensión, **cuando** se sube, **entonces** se rechaza indicando el motivo y no se crea ningún análisis (RF-01, 8.1).
3. **Dado** un análisis en curso, **cuando** se consulta, **entonces** su estado es uno de estos: en cola, procesando (con % de avance), esperando confirmación, terminado, o error con su motivo (RF-04).
4. **Dado** un análisis en «error», **cuando** la analista reintenta mientras dure la retención, **entonces** se relanza sin volver a subir el audio (8.1).
5. **Antes** de subir, la pantalla muestra el aviso de privacidad de la sección 8.4.

---

### Historia 2 - Confirmar las voces (Prioridad: P1)

La analista escucha los fragmentos de cada hablante, ve la propuesta y su confianza, y elige femenino, masculino o indeterminado. Hasta que confirma todas las voces presentes, no hay resultados.

**Por qué esta prioridad**: es Must (RF-07) y es la supervisión humana en la que se apoya todo el apartado ético (RN-02, sección 4.3).

**Prueba independiente**: con datos de ejemplo, se comprueba que la pantalla no deja ver resultados hasta confirmar todas las voces y que guarda si cada etiqueta vino del modelo o de una persona.

**Escenarios de aceptación**:

1. **Dado** un análisis «esperando confirmación», **cuando** se abre Confirmar voces, **entonces** hay una tarjeta por hablante presente con sus fragmentos, la propuesta, la confianza y tres opciones: femenino, masculino e indeterminado (RF-07, 8.2).
2. **Dado** el modo manual, **cuando** se abre la pantalla, **entonces** las tarjetas no muestran propuesta (RF-08).
3. **Dado** que falta alguna voz presente por confirmar, **cuando** la analista intenta ver resultados, **entonces** no puede (RF-07, RN-01).
4. **Dada** una etiqueta confirmada, **cuando** se guarda, **entonces** consta si coincide con la del modelo o la ha fijado una persona (RF-07).
5. La pantalla cubre los estados «propuesta dudosa», «hablante con poco audio» y «todo confirmado» (8.2) y muestra el texto de la sección 8.4.

---

### Historia 3 - Ver y escuchar los resultados (Prioridad: P1)

La analista ve el resumen del episodio y puede escuchar cada interrupción.

**Por qué esta prioridad**: es lo que el jurado ve en la demo y es Must (RF-17, RF-18).

**Prueba independiente**: con el JSON de ejemplo «con muchas interrupciones», se comprueba que aparecen todas las piezas y que cada interrupción se puede escuchar.

**Escenarios de aceptación**:

1. **Dado** un análisis terminado, **cuando** se abre Resultados, **entonces** aparecen las tarjetas de presencia e índices, la línea de tiempo por hablante con los solapamientos, el gráfico de tiempo por hablante y la tabla de interrupciones (RF-17).
2. **Dada** una interrupción de la tabla, **cuando** se pulsa «escuchar», **entonces** suena un fragmento que empieza como mucho 1 s antes del evento, acaba después y dura 15 s como máximo [VALIDAR] (RF-18).
3. **Dado** cualquier número de la pantalla, **cuando** se abre, **entonces** muestra su fórmula y lleva a sus fragmentos (RN-06, 8.3).
4. **Dado** un episodio sin voces femeninas o con un índice «no aplicable», **cuando** se muestra, **entonces** aparece el texto de la sección 8.4, nunca un 0 (RN-13).
5. Los hablantes aparecen como «Hablante n» (RN-10), sin rankings de personas, y la pantalla muestra el texto «Estos datos describen este episodio, no a las personas…» (8.3, 8.4).

---

### Historia 4 - Ejemplos precalculados (Prioridad: P2)

Cualquier persona, incluido el jurado, elige un episodio ya analizado y ve sus resultados al momento.

**Por qué esta prioridad**: es Must (RF-02), pero depende de que el recorrido de la prioridad 1 funcione (plan, Parte 0).

**Prueba independiente**: se elige un ejemplo y se mide el tiempo hasta ver los resultados.

**Escenarios de aceptación**:

1. **Dado** un ejemplo precalculado, **cuando** se elige, **entonces** sus resultados aparecen en 2 s o menos sin llamar a servicios externos (RF-02, RNF-02).
2. **Dado** un ejemplo, **cuando** se abre, **entonces** se salta la confirmación, porque ya se hizo al prepararlo (8.1).

---

### Historia 5 - Página «Cómo funciona» (Prioridad: P2)

Quien usa el sistema entiende qué mide, cómo y con qué límites.

**Por qué esta prioridad**: es Must (RF-22) y pesa en transparencia y comunicación (anexo B).

**Prueba independiente**: inspección de la página frente a la lista de contenidos de RF-22.

**Escenarios de aceptación**:

1. **Dada** la página, **cuando** se lee, **entonces** contiene definiciones, fórmulas, exactitud por grupo y limitaciones (RF-22), y explica que el sistema no escucha lo que se dice (plan, tarea C11).

---

### Historia 6 - Borrar el audio al cumplirse la retención (Prioridad: P2)

Pasado el plazo, el audio y sus fragmentos desaparecen y solo quedan datos agregados.

**Por qué esta prioridad**: es Must (RF-23, RNF-12) y es la base de la privacidad del sistema.

**Prueba independiente**: una prueba deja pasar el plazo y revisa el disco.

**Escenarios de aceptación**:

1. **Dado** un análisis cuyo plazo de retención [NEEDS CLARIFICATION: plazo de D-08, abierta en el anexo C] se ha cumplido, **cuando** se revisa el disco, **entonces** no queda ni el audio ni sus fragmentos, solo datos agregados (RF-23).

---

### Casos límite

- **Archivo con extensión de audio que no es audio:** se rechaza por su contenido (RF-01, RNF-10).
- **Archivo malicioso o mal formado:** se rechaza sin colgar el servicio; el nombre del archivo lo genera el sistema (RNF-10).
- **Petición de un fragmento de más de 15 s:** se rechaza, para que no se pueda descargar el audio completo (9.3).
- **Hablante con poco audio:** la tarjeta lo indica (8.2).
- **Demo pública:** sin autenticación, solo debe ofrecer los ejemplos precalculados (2.3). [NEEDS CLARIFICATION: ¿admite subidas la demo pública? Es parte de D-08.]

## Requisitos *(obligatorio)*

### Requisitos funcionales

- **FR-001**: El sistema DEBE aceptar audios mp3, wav, m4a, ogg y flac, comprobar su tipo real por el contenido y rechazar con motivo los que no lo son (RF-01, Must; RNF-10).
- **FR-002**: El sistema DEBE aplicar límites de tamaño y duración, dar al archivo un nombre generado por el sistema y procesarlo sin shell y con tiempo máximo (RNF-10, Must).
- **FR-003**: El sistema DEBE mostrar el estado del análisis: en cola, procesando con % de avance, esperando confirmación, terminado, o error con su motivo (RF-04, Must).
- **FR-004**: El sistema DEBE permitir reintentar un análisis en error sin volver a subir el audio, mientras dure la retención (8.1).
- **FR-005**: El sistema DEBE mostrar por hablante sus fragmentos, la propuesta, la confianza y las tres opciones, y no mostrar resultados hasta confirmar todas las voces presentes (RF-07, Must).
- **FR-006**: El sistema DEBE guardar si cada etiqueta final viene del modelo o de una persona (RF-07).
- **FR-007**: El sistema DEBE mostrar tarjetas de presencia e índices, línea de tiempo por hablante, gráfico de tiempo y tabla de interrupciones (RF-17, Must).
- **FR-008**: El sistema DEBE permitir escuchar cada interrupción con un fragmento que empieza como mucho 1 s antes, acaba después y dura 15 s como máximo (RF-18, Must).
- **FR-009**: El sistema DEBE ofrecer episodios de ejemplo precalculados cuyos resultados aparecen en 2 s o menos (RF-02, RNF-02, Must).
- **FR-010**: El sistema DEBE tener una página «Cómo funciona» con definiciones, fórmulas, exactitud por grupo y limitaciones (RF-22, Must).
- **FR-011**: El sistema DEBE borrar el audio y los fragmentos al cumplirse la retención y conservar solo datos agregados (RF-23, Must).
- **FR-012**: La interfaz DEBE estar en español (RNF-19, Must) y usar los textos clave de la sección 8.4.
- **FR-013**: La interfaz DEBE seguir los principios de 8.3: cada número abre su fórmula, la incertidumbre se ve, paleta neutra sin rosa ni azul, «Hablante n» por defecto, sin rankings de personas y «voz percibida como femenina» en vez de «mujer».
- **FR-014**: La interfaz DEBERÍA cumplir WCAG 2.1 AA en contraste, teclado y textos alternativos, y el color nunca es la única señal (RNF-14, Should).
- **FR-015**: Los tipos de datos de la web DEBEN generarse a partir de la descripción de la API, nunca copiarse (RD-02).

### Entidades clave

Los nombres de campo definitivos los fija el contrato de datos (`docs/contrato_de_datos.md`), todavía pendiente.

- **Análisis**: identificador, estado, % de avance, motivo de error y fecha de subida (para la retención).
- **Hablante para confirmar**: «Hablante n», fragmentos, propuesta, confianza y etiqueta confirmada con su origen.
- **Resultado del episodio**: métricas, índices e interrupciones que calcula la feature 002.
- **Ejemplo precalculado**: nombre, origen y licencia del audio, y su resultado ya confirmado.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: Un resultado precalculado aparece en 2 s o menos, medido en el navegador (RNF-02, Must).
- **SC-002**: 2 de 3 personas ajenas al equipo completan un análisis de ejemplo sin ayuda en menos de 3 min (RNF-15, Should).
- **SC-003**: Una persona confirma las voces de un episodio en menos de 2 min (supuesto S5, validado con RNF-15).
- **SC-004**: La revisión automática de accesibilidad no da errores de nivel AA, y el recorrido completo se puede hacer solo con el teclado (RNF-14, Should).
- **SC-005**: Las pruebas con archivos maliciosos y mal formados se rechazan todas sin colgar el servicio (RNF-10, Must).
- **SC-006**: Pasado el plazo de retención, una prueba que revisa el disco no encuentra ni audios ni fragmentos (RF-23, RNF-12).
- **SC-007**: Ninguna petición devuelve más de 15 s de audio (9.3).

## Supuestos

- **Rutas:** las de la sección 9.3 del funcional; la descripción de la API que publica el backend es la fuente de los tipos de la web (RD-02).
- **Tecnología decidida:** React, Vite y TypeScript con pnpm (D-02).
- **Un solo rol:** la analista, sin autenticación, en el MVP (2.3).
- **Trabajo en paralelo:** la web empieza en modo falso con los 3 JSON de ejemplo del contrato (plan, Parte 8).
- **Contrato:** depende de `docs/contrato_de_datos.md`, todavía pendiente.
- **Fuera de esta feature:** preparar el audio, separar voces, proponer la voz y elegir los fragmentos (001), y calcular métricas e interrupciones (002).
