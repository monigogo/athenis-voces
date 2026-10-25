# Documento funcional — athenis-voces

Oct 23, 2026 · @moni

## 0. Control del documento

Versión 0.2 en borrador: completad los campos [COMPLETAR] durante el reto y congelad la versión 1.0 el miércoles 28 de octubre (tarea B20 del plan definitivo).

| Campo | Valor |
| --- | --- |
| Proyecto | [**athenis-voces**](https://github.com/monigogo/athenis-voces) |
| Reto | Mujeres por la IA Abierta , Comunidad IA de Código Abierto |
| Versión y estado | 0.2 · borrador |
| Autoras | Monica Gomez, Aroa Mateo, Vania Carlos |
| Aprobación | Las tres autoras (sección 12.5) |
| Repositorio | <https://github.com/monigogo/athenis-voces.git> |
| Documentos relacionados | Bases del reto · Plan definitivo · docs/contrato\_de\_datos.md |

**Convenciones**

- **Identificadores:** RF requisito funcional · RNF requisito no funcional · RN regla de negocio · RD regla de desarrollo · C restricción · R riesgo · S supuesto · M métrica de calidad · D decisión. Un identificador no se reutiliza: lo que se elimina se marca «retirado».
- **Obligación:** «debe» = obligatorio para aceptar el MVP; «debería» = solo se omite con motivo registrado en el anexo C; «puede» = opcional.
- **Prioridad (MoSCoW):** Must imprescindible · Should importante · Could deseable · Won't fuera de esta versión.
- **Verificación:** P prueba automática · D demostración · I inspección de código o documento · A análisis con datos.
- **Origen:** B bases del reto · R rúbrica · E decisión del equipo.
- **Marcadores:** [COMPLETAR] dato que falta · [DECIDIR] decisión abierta en el anexo C · [VALIDAR] objetivo propuesto que debe confirmar una medición.

**Regla de rigor:** ningún requisito entra sin un criterio de aceptación verificable, y ninguna cifra sin su método de medición o su fuente.

**Registro de cambios**

| Fecha | Versión | Cambio | Autora |
| --- | --- | --- | --- |
| 24 oct 2026 | 0.2 | El sistema analiza solo la voz: sin transcripción ni LLM. Nombre athenis-voces. Datos: grabaciones propias, corpus AMI y una sesión del Congreso. Tres tipos de interrupción. Decididas D-03, D-04, D-05 y D-07; nuevas D-10 a D-12 | Monica Gomez |
| 23 oct 2026 | 0.1 | Plantilla inicial | Monica Gomez |

## 1. Introducción y alcance

athenis-voces analiza la voz de un audio, nunca lo que se dice, y responde a tres preguntas: si hay voces femeninas, qué papel tienen en la conversación y si se las interrumpe más. La parte sensible, etiquetar cada voz, queda bajo supervisión humana.

### 1.1 Propósito del documento

Es el acuerdo entre las tres integrantes sobre qué debe hacer el sistema y cómo se comprueba. El cómo técnico está en el plan definitivo y en el contrato de datos. La presentación y el README parten de este documento.

### 1.2 Objetivos

| ID | Objetivo específico | Se comprueba con |
| --- | --- | --- |
| OE1 | Detectar si hay voces femeninas y cuantificar su tiempo de habla | RF-05 a RF-07, RF-12 |
| OE2 | Medir el rol protagonista: posición, turnos largos y respeto del turno | RF-13, RF-14, RF-16 y catálogo 6.7 |
| OE3 | Detectar y clasificar interrupciones y comparar su incidencia por grupo | RF-14 a RF-16 |
| OE4 | Explicar cada cifra con su fórmula y su fragmento de audio | RN-06, RF-18, RF-22 |
| OE5 | Publicar una solución abierta y reproducible por terceras personas | RNF-07, RNF-18 |

### 1.3 Alcance

**Dentro del MVP**

- Modalidad audio: el reto permite elegir una sola.
- Conversaciones grabadas de cualquier sector, analizadas por episodio: demo en español con grabaciones propias y evaluación también con reuniones en inglés del corpus AMI.
- Interfaz web, API y ejecución reproducible con Docker.

**Fuera del MVP, con su motivo**

- Vídeo, texto y el contenido de lo que se dice: el reto exige una sola modalidad y el sistema solo escucha la voz, sin transcribir.
- Identificar a las personas por su nombre o por su voz: no lo necesita el objetivo y aumenta el riesgo legal.
- Inferir identidad de género, edad u origen: la voz no los determina (sección 10.2).
- Análisis en directo, aplicación móvil y cuentas de usuario: no caben en el plazo.
- Evaluar a personas concretas: es un uso prohibido (sección 10.6).

**Hoja de ruta:** interfaz en catalán, euskera y gallego; vídeo; análisis interseccional; análisis en directo; comparar episodios y exportar resultados; servidor MCP público.

### 1.4 Referencias

- Bases del reto «Mujeres por la IA Abierta».
- Reglamento (UE) 2024/1689 de Inteligencia Artificial y su modificación por el Reglamento (UE) 2026/1744 (Ómnibus Digital).
- Reglamento (UE) 2016/679 (RGPD) y Ley Orgánica 3/2018 (LOPDGDD).
- Directrices éticas para una IA fiable, Grupo de Expertos de Alto Nivel de la Comisión Europea (2019).
- Directiva (UE) 2019/790 sobre derechos de autor en el mercado único digital.

## 2. Usuarios y roles

El MVP tiene un único rol operativo, la analista. En producción se separan analista, revisora, administradora y lectora. Las personas cuya voz se analiza no usan el sistema, pero son la parte más afectada.

### 2.1 Perfiles de usuaria

| ID | Perfil | Necesidad | Qué hace en el sistema |
| --- | --- | --- | --- |
| U1 | Responsable de igualdad o de contenidos en un medio | Medir la paridad de su catálogo | Analiza episodios y revisa sus resultados |
| U2 | Productora de podcast | Revisar un episodio antes de publicarlo | Analiza un episodio y escucha los casos |
| U3 | Investigadora u observatorio de igualdad | Datos agregados comparables y una metodología clara | Revisa los resultados y «cómo funciona» |
| U4 | Jurado del reto | Comprobar que funciona y que es riguroso | Usa los ejemplos precalculados y lee la metodología |

[VALIDAR U1–U3 con al menos una conversación real antes del pitch: un perfil sin validar es una hipótesis, no un usuario.]

### 2.2 Partes afectadas

| ID | Parte | Qué se le debe garantizar |
| --- | --- | --- |
| A1 | Personas cuya voz se analiza | No ser identificadas; poder conocer el análisis; que no se fije su género sin revisión humana |
| A2 | Titulares de derechos del audio | Uso autorizado o amparado por una excepción legal (sección 10.4) |

Criterio: cada decisión ética se justifica frente a A1, no solo frente a quien usa el sistema.

### 2.3 Roles y permisos del sistema

| Rol | Puede | No puede | En el MVP |
| --- | --- | --- | --- |
| Analista | Subir audio, confirmar etiquetas y ver resultados | Ver análisis de otras analistas | Sí: único rol, sin autenticación |
| Revisora | Confirmar o corregir etiquetas y casos dudosos | Borrar análisis | No |
| Administradora | Configurar modelos, límites y retención | Ver contenidos sin un motivo registrado | No |
| Lectora | Ver resultados agregados | Escuchar fragmentos de audio | No |

Sin autenticación, el MVP desplegado en público solo debe ofrecer los ejemplos precalculados. La subida de audio real queda en entorno local [DECIDIR D-08 si la demo pública admite subidas].

### 2.4 Roles del equipo (RACI)

R realiza · A responde y aprueba (una por fila) · C consultada · I informada. B = Monica Gomez; A = Vania Carlos; C = Aroa Mate.

| Trabajo | Persona A (audio y voz) | Persona B (análisis y evaluación) | Persona C (producto) |
| --- | --- | --- | --- |
| Separación de voces y propuesta de voz | A | C | I |
| Métricas, interrupciones e índices | C | A | I |
| API y web | I | C | A |
| Contrato de datos | C | A | C |
| Anotación de interrupciones | R | I | A |
| Evaluación y tabla de equidad | C | A | I |
| Ética y normativa | A | C | C |
| Plan de producción | A | I | C |
| Seguridad (scripts e instrucción del agente de seguridad; hooks en B) | A | R | C |
| Docker | C | A | C |
| README y documentación de código abierto | A | C | C |
| Presentación y vídeo | R | R | A |
| Entrega y etiqueta v1.0 | C | A | C |

B diseña las reglas de interrupción, así que no anota el conjunto de prueba: así se evita el sesgo de confirmación (sección 11.2).

## 3. Contexto del proyecto

El reto pide medir con IA abierta la presencia y el protagonismo de las mujeres en contenidos digitales. Elegimos audio porque en podcasts, reuniones y actos públicos el protagonismo se ve en quién habla, quién abre y cierra y a quién se interrumpe. El sistema lo mide solo con la voz, sin analizar lo que se dice.

### 3.1 Problema

[COMPLETAR con un dato verificable y su fuente enlazada. Fuente candidata: el informe más reciente del Global Media Monitoring Project; comprobad la cifra y el año en el propio informe antes de usarla.]

Contar minutos no basta: una mujer puede hablar mucho y aun así no abrir ni cerrar nunca la conversación, no tener turnos largos o ser la más interrumpida. Por eso medimos también el papel que ocupa (sección 6.7).

### 3.2 Marco del reto

- **Organiza:** Secretaría de Estado de Digitalización e Inteligencia Artificial (SEDIA), dentro de la Comunidad IA de Código Abierto.
- **Colaboran:** UPC e IDEAI, COEINF y donesCOEINF, y OVHcloud.
- **Recursos:** máquina virtual compartida con JupyterLab y 2 GPU NVIDIA V100S, y un token gratuito de OVHcloud AI Endpoints con límites de peticiones.
- **Evaluación:** 60 % valoración técnica y 40 % propuesta y defensa (detalle en el anexo B). Plazos en la sección 12.4.

### 3.3 Estado del arte y diferenciación

| Enfoque existente | Qué resuelve | Qué añadimos |
| --- | --- | --- |
| inaSpeechSegmenter (INA), creado para estudios de igualdad en radio y televisión francesas | Tiempo de habla por voz femenina y masculino | Rol protagonista, interrupciones, confirmación humana y validación en español |
| Diarización genérica (pyannote, servicios de transcripción) | Quién habla cuándo | Métricas con perspectiva de género y explicación de cada cifra |
| Recuento manual en observatorios | Rigor, pero lento y caro | La misma metodología, automatizada y repetible, con revisión humana |

[COMPLETAR el sábado 24: 30 minutos buscando antecedentes. No afirméis que no existe nada parecido; citad lo encontrado y explicad la diferencia.]

### 3.4 Supuestos

| ID | Supuesto | Cómo y cuándo se valida |
| --- | --- | --- |
| S1 | La demo es en español; la evaluación usa también reuniones en inglés del corpus AMI | Confirmado por el equipo el 24 oct 2026 |
| S2 | Hay audios con licencia suficiente para desarrollar, evaluar y enseñar en la demo | Inventario en docs/datos.md (tarea A09) |
| S3 | El token de AI Endpoints aguanta el uso de los agentes de programación | Medir el consumo real el sábado 24 |
| S4 | La GPU de Monica, o de reserva la V100S con PyTorch para CUDA 12.6, ejecuta pyannote en los audios largos | Prueba el domingo 25 (tarea B13) |
| S5 | Una persona confirma las voces de un episodio en menos de 2 minutos | Prueba de usabilidad (RNF-15) |

Un supuesto que falla se convierte en riesgo (sección 4.2) y se anota en el anexo C.

### 3.5 Dependencias

Hugging Face (descarga del modelo de diarización, con acceso condicionado) · GPU de Monica y, de reserva, la V100S · organización de GitHub de la Comunidad · corpus AMI y anotaciones de BUT · pistas de datos de la web del reto. OVHcloud AI Endpoints solo se usa para los agentes de programación, no para analizar.

## 4. Restricciones, riesgos y clasificación

Las restricciones duras son el plazo, el código abierto y la normativa. El riesgo que más condiciona el diseño es inferir el sexo a partir de la voz, porque afecta a la vez a la clasificación legal, a la equidad y a la confianza en el resultado.

### 4.1 Restricciones

| ID | Restricción | Origen | Consecuencia en el diseño |
| --- | --- | --- | --- |
| C1 | Entrega antes del 30 de octubre de 2026 a las 08:00 | B | Congelación de funciones el martes 27 de octubre |
| C2 | Repositorio público en la organización de la Comunidad, con licencia OSI o FSF | B | Ningún audio ni dato personal en el repositorio |
| C3 | Todo el software, de código abierto | E | Inventario automático de licencias |
| C4 | LLM agnóstico y compatible con modelos abiertos, si se usan | B | No aplica: el sistema no usa LLM |
| C5 | Backend con uv y frontend con pnpm | E | Dos gestores separados, sin mezclarlos |
| C6 | GPU V100S: sin bfloat16 y con PyTorch para CUDA 12.6 | B | Versión de PyTorch fijada si pyannote corre en la V100S |
| C7 | Token de AI Endpoints con límites de peticiones | B | Solo lo usan los agentes de programación |
| C8 | Tres personas y unas 35 horas por persona, del 24 al 29 de octubre | E | Priorización MoSCoW estricta |
| C9 | Marco ético europeo y normativa vigente | B | Secciones 4.3 y 10 |

### 4.2 Riesgos

Estimación inicial del equipo [VALIDAR], que se revisa en cada punto de encuentro. Cuando un riesgo se materializa, se activa su plan B y se anota en el anexo C.

[COMPLETAR diagrama: mapa de riesgos · probabilidad × impacto · 11 riesgos vigentes]

Solo R5 y R9 combinan probabilidad e impacto altos. Revisad la posición de cada riesgo en cada punto de encuentro.

| ID | Riesgo | Señal de alerta | Mitigación | Plan B | Resp. |
| --- | --- | --- | --- | --- | --- |
| R1 | La propuesta de voz falla más con un grupo | Diferencia de error entre grupos mayor que el umbral de RNF-06 | Datos equilibrados, zona dudosa y confirmación humana | Publicar el sesgo y ampliar la zona dudosa | A |
| R2 | El sistema encaja como alto riesgo en la Ley de IA | Análisis 4.3 o respuesta de las mentoras | Modo manual y confirmación humana; evaluación documentada | Solo modo manual en producción | A |
| R3 | La diarización no funciona en la GPU | Error de arquitectura o «no kernel image» | En la V100S, PyTorch para CUDA 12.6, versión 2.14 o anterior | La otra GPU (la de Monica o la V100S) o fragmentos más cortos en CPU | A |
| R4 | Se agotan los límites del token de los agentes de programación | Respuestas 429 o vacías | Un modelo solo para los agentes; la aplicación no hace llamadas | Programar sin agente mientras se recupera | B |
| R5 | Los solapamientos se detectan mal y se subestiman las interrupciones | Exhaustividad baja en desarrollo | Motor con detección de solapamiento; ajuste en desarrollo | Declarar el límite y mostrar casos para revisar | B |
| R6 | Retirado en la v0.2: el sistema no usa LLM | — | — | — | — |
| R7 | Audios sin licencia para la demo pública | Inventario de datos incompleto | Elegir fuentes con licencia el sábado 24 | Grabación propia con consentimiento | A |
| R8 | La integración llega tarde | El domingo a las 21:00 no funciona el recorrido completo | Contrato primero, datos de ejemplo y puntos de integración fijos | Recortar a los RF Must | B |
| R9 | Los entregables se comen el último día | Sin guion de vídeo el domingo por la noche | Guiones el domingo (B15) y tomas de la demo el miércoles (C14) | Vídeo con capturas y voz en off | C |
| R10 | Una clave o un dato personal llega al repositorio público | Aviso de gitleaks o del agente de seguridad | Hooks, .gitignore y revisión | Revocar la clave y limpiar el historial | A |
| R11 | Se generalizan conclusiones a partir de pocos episodios | Frases del tipo «las mujeres en los podcasts…» | RN-12; n e intervalos siempre visibles | Revisar los textos de la presentación | B |
| R12 | Se atribuye a una persona un género que no es el suyo | Etiqueta corregida después de publicar | Autopresentación pública como criterio; «indeterminado» | Corregir y retirar el resultado afectado | A |

### 4.3 Clasificación según la Ley de IA

Conclusión provisional: no es una práctica prohibida, pero inferir el sexo a partir de la voz podría convertirlo en un sistema de alto riesgo. El modo manual reduce esa exposición. Esto no es asesoramiento jurídico [VALIDAR con las mentoras de marco ético].

1. **¿Práctica prohibida (art. 5.1.g)?** No. La prohibición de categorización biométrica cubre raza, opiniones políticas, afiliación sindical, convicciones religiosas o filosóficas, vida sexual y orientación sexual. El sexo no está en esa lista.
2. **¿Categorización biométrica?** Probablemente sí, si un modelo asigna a cada persona una categoría a partir de los rasgos de su voz.
3. **¿Alto riesgo (anexo III, punto 1.b)?** Posible. El anexo incluye la categorización biométrica según atributos sensibles o protegidos inferidos, y el sexo es una característica protegida en el derecho antidiscriminatorio de la UE. Tras el Ómnibus Digital, esas obligaciones se aplican desde el 2 de diciembre de 2027.
4. **¿Excepción del art. 6.3?** Se puede defender como tarea preparatoria de una valoración humana. No aplica si hay elaboración de perfiles de personas físicas, y obliga a documentar la evaluación (art. 6.4).
5. **Durante el reto:** es un prototipo de investigación; valorad si encaja en la exclusión de investigación y desarrollo del art. 2.

**Diseño que se deriva**

- **Modo manual (RF-08):** ningún modelo infiere el sexo; la persona etiqueta después de escuchar. La diarización solo agrupa voces dentro del audio, sin identificar a nadie ni clasificar por atributos.
- **Modo asistido (RF-06 y RF-07):** el modelo propone y la persona decide. Se usa en investigación y para evaluar el modelo.
- **Decisión (D-04):** modo manual por defecto en producción hasta tener la evaluación legal; en el MVP, modo asistido con confirmación humana siempre.

### 4.4 Clasificación de los datos

| Dato | Clase | Dónde vive | Retención | ¿Al repositorio? |
| --- | --- | --- | --- | --- |
| Audio original y fragmentos | Personal (voz) | Servidor de análisis | Plazo de D-08 [DECIDIR] | No |
| Etiqueta de voz confirmada | Personal (atributo inferido o declarado) | Resultado del análisis | Con el resultado | No |
| Métricas por «Hablante n» | Seudonimizada | Resultado del análisis | [DECIDIR] | Solo de ejemplos con licencia |
| Etiquetas de evaluación | Seudonimizada, sin texto ni nombres | evaluacion/etiquetas | Proyecto | Sí, si la fuente lo permite |
| Grabaciones propias del equipo | Personal (voz), con consentimiento por escrito | Ordenadores del equipo y servidor de la demo | Hasta el final del reto [DECIDIR] | No |
| Reuniones del corpus AMI | Personal (voz) de terceros, licencia CC BY 4.0 | datos/, en local; se descargan con scripts/descargar\_datos.sh | Proyecto | No |
| Sesión del Congreso | Personal (voz) de cargos públicos; reutilización citando la fuente [VALIDAR] | datos/, en local | Proyecto | No |
| Claves (token de Hugging Face) | Secreto | .env | — | Nunca |

El sexo no es una categoría especial del art. 9 del RGPD. La voz solo lo es cuando se trata para identificar de forma unívoca, y el sistema no identifica a nadie.

## 5. Reglas del proyecto

Las reglas de negocio fijan cómo se cuenta cada cosa y no cambian sin pasar por el anexo C. Las reglas de desarrollo protegen la calidad del código y el repositorio público.

### 5.1 Reglas de negocio

| ID | Regla | Motivo |
| --- | --- | --- |
| RN-01 | Una voz cuenta como presente si suma al menos 10 s de habla [VALIDAR] y tiene al menos 3 tramos de 3 s o más sin solaparse con nadie, para poder escucharla (D-18); las que no lo cumplen no se confirman y su tiempo se muestra aparte en el resultado (D-15) | No contar ruidos ni un «hola» suelto, sin esconder a nadie que habló |
| RN-02 | La etiqueta final de voz la fija una persona; el modelo solo propone | Supervisión humana y perspectiva de género |
| RN-03 | Las etiquetas posibles son femenino, masculino e indeterminado; «indeterminado» nunca se reparte entre las otras dos | No forzar el binarismo ni inflar porcentajes |
| RN-04 | Los porcentajes por grupo se calculan sobre el tiempo de voces etiquetadas; el tiempo indeterminado se informa aparte | Denominador transparente |
| RN-05 | Retirada en la v0.2: el sistema no usa LLM; todas las cifras las calcula el código | Exactitud y reproducibilidad |
| RN-06 | Toda cifra mostrada lleva a su fórmula y a sus fragmentos de audio | Explicabilidad |
| RN-07 | Hay tres tipos de solapamiento (definidos en 6.7); solo «con éxito» e «intento» cuentan como interrupción | Las señales de escucha no quitan la palabra |
| RN-08 | Las tasas de interrupción se dan por cada 10 minutos de habla de la persona interrumpida | Quien habla menos tiene menos ocasiones de ser interrumpida |
| RN-09 | La representación se compara con lo proporcional, no con el 50 % | Evitar conclusiones falsas cuando hay pocas mujeres |
| RN-10 | Los hablantes aparecen como «Hablante n»; un nombre visible solo si la usuaria lo escribe | Minimización de datos |
| RN-11 | Retirada en la v0.2: no hay juez LLM | — |
| RN-12 | Los resultados de un episodio no se generalizan; toda comparación indica el número de episodios y de minutos | Rigor estadístico |
| RN-13 | Si un grupo no tiene voces o tiempo, sus índices se muestran como «no aplicable» | Nunca dividir por cero ni mostrar un 0 engañoso |

### 5.2 Reglas de desarrollo

| ID | Regla |
| --- | --- |
| RD-01 | uv solo en backend/ y pnpm solo en frontend/; prohibidos pip install, npm install y yarn |
| RD-02 | El contrato de datos tiene una sola fuente, contrato.py; los tipos del frontend se generan desde la API, nunca se copian |
| RD-03 | Nadie sube a main directamente: cada cambio pasa la revisión de otra integrante, los hooks desde que existen (sábado 24) y el agente revisor desde que existe su instrucción (lunes 26) |
| RD-04 | Ningún audio, transcripción, nombre real ni clave entra en el repositorio |
| RD-05 | Umbrales y pesos se ajustan solo con el conjunto de desarrollo; el de prueba se usa una vez por versión (11.3) |
| RD-06 | Todo cambio de regla de negocio o de umbral se registra en el anexo C con motivo y fecha |
| RD-07 | Versiones de librerías y modelos fijadas |
| RD-08 | Nunca --no-verify: un hook en rojo se arregla, no se salta |
| RD-09 | Los agentes de IA no leen .env ni suben código sin confirmación humana; nunca deciden reglas de negocio ni umbrales |
| RD-10 | Definición de hecho: código, pruebas, documentación del cambio, hooks en verde y revisión aprobada |
| RD-11 | Una rama numerada por feature, como las que crea Spec Kit |

## 6. Requisitos funcionales

Hay 26 requisitos: 15 Must, 1 Should y 10 Won't en esta versión. El MVP se acepta solo si los 15 Must pasan su verificación (sección 12.3).

### 6.1 Entrada y seguimiento

| ID | Requisito | Prior. | Criterio de aceptación | Verif. | Resp. |
| --- | --- | --- | --- | --- | --- |
| RF-01 | Subir un audio en mp3, wav, m4a, ogg o flac | Must | Un archivo válido dentro de los límites [COMPLETAR tamaño y duración máximos] crea un análisis «en cola»; un archivo que no es audio, comprobado por su contenido y no por la extensión, se rechaza indicando el motivo | P | C |
| RF-02 | Elegir un episodio de ejemplo precalculado | Must | Sus resultados aparecen en 2 s o menos sin llamar a servicios externos | D | C |
| RF-03 | Normalizar el audio a WAV mono de 16 kHz | Must | La duración de salida coincide con la de entrada ± 0,1 s | P | A |
| RF-04 | Seguir el estado del análisis | Must | Estados: en cola, procesando con % de avance, esperando confirmación, terminado, y error con su motivo | P | C |

### 6.2 Voces

| ID | Requisito | Prior. | Criterio de aceptación | Verif. | Resp. |
| --- | --- | --- | --- | --- | --- |
| RF-05 | Separar hablantes y detectar habla simultánea | Must | Devuelve turnos y solapamientos con el formato del contrato, con pyannote en local | P y A (M-01) | A |
| RF-06 | Proponer una etiqueta de voz por hablante, con su confianza | Must en modo asistido (D-03: inaSpeechSegmenter) | Probabilidad entre 0 y 1; en la zona dudosa [VALIDAR 0,35–0,65] la propuesta es «indeterminado» | A (M-02, M-03) | A |
| RF-07 | Confirmar o corregir cada etiqueta escuchando muestras | Must | Al menos 3 fragmentos de 3 a 5 s por hablante; opciones femenino, masculino e indeterminado; queda registrado si la etiqueta vino del modelo o de una persona; no hay resultados hasta confirmar todas las voces presentes (RN-01) | D y P | C |
| RF-08 | Modo manual, sin propuesta automática | Should (D-04 decidida) | Con el modo activo no se ejecuta ningún clasificador de voz y la persona etiqueta sin propuesta previa | P | A |

### 6.3 Transcripción y señales de conversación (Won't en esta versión)

| ID | Requisito | Prior. | Criterio de aceptación | Verif. | Resp. |
| --- | --- | --- | --- | --- | --- |
| RF-09 | Transcribir con tiempos por palabra | Won't | El sistema solo escucha la voz y no transcribe (D-10) | — | — |
| RF-10 | Asignar cada palabra a su hablante | Won't | Depende de RF-09 | — | — |
| RF-11 | Extraer con el LLM preguntas, presentaciones, cargos y cesiones de palabra | Won't | Necesita analizar lo que se dice (D-10) | — | — |

### 6.4 Métricas e interrupciones

| ID | Requisito | Prior. | Criterio de aceptación | Verif. | Resp. |
| --- | --- | --- | --- | --- | --- |
| RF-12 | Calcular presencia y participación (6.7) | Must | Coinciden con el cálculo a mano en 3 casos sintéticos | P | B |
| RF-13 | Calcular la posición: abre, cierra y presenta | Must abre y cierra; Won't presenta | Igual que RF-12 | P | B |
| RF-14 | Detectar interrupciones por reglas y clasificarlas en tres tipos | Must | Un caso sintético de cada tipo se clasifica bien; F1 publicado (M-05) | P y A | B |
| RF-15 | Resolver los casos dudosos con un juez LLM | Won't | El sistema no usa LLM (D-10) | — | — |
| RF-16 | Calcular el ratio de representación, la brecha de interrupción y el índice de protagonismo | Must los dos primeros; Should el tercero | Fórmula visible; una prueba cubre RN-13 | P | B |

### 6.5 Resultados y explicación

| ID | Requisito | Prior. | Criterio de aceptación | Verif. | Resp. |
| --- | --- | --- | --- | --- | --- |
| RF-17 | Mostrar los resultados de un episodio | Must | Tarjetas de presencia e índices, línea de tiempo por hablante, gráfico de tiempo y tabla de interrupciones | D | C |
| RF-18 | Escuchar el fragmento de cada interrupción | Must | Empieza como mucho 1 s antes del evento y acaba después; 15 s como máximo [VALIDAR] | D | C |
| RF-19 | Generar un informe narrativo con el LLM | Won't | El sistema no usa LLM (D-10) | — | — |
| RF-20 | Comparar episodios | Won't | Hoja de ruta | — | — |
| RF-21 | Exportar resultados en JSON y CSV | Won't | Hoja de ruta | — | — |
| RF-22 | Página «cómo funciona» | Must | Definiciones, fórmulas, exactitud por grupo y limitaciones | I | C |

### 6.6 Privacidad y configuración

| ID | Requisito | Prior. | Criterio de aceptación | Verif. | Resp. |
| --- | --- | --- | --- | --- | --- |
| RF-23 | Borrar audio y fragmentos al cumplirse la retención | Must | Pasado el plazo solo quedan datos agregados; lo comprueba una prueba que revisa el disco | P | C |
| RF-24 | Cambiar proveedor y modelo de LLM por configuración | Won't | No aplica: el sistema no usa LLM (D-10) | — | — |
| RF-25 | Servidor MCP para analizar, ver resultados y comparar | Won't | Hoja de ruta | — | — |
| RF-26 | Trazas del LLM con Langfuse autoalojado | Won't | No aplica: el sistema no usa LLM (D-05) | — | — |

### 6.7 Catálogo de métricas de dominio

Es la propuesta conceptual que pide el reto, medida solo con la voz: cuatro dimensiones (presencia, participación, posición y respeto del turno) y tres índices que las resumen. MD-09 a MD-13 se retiran en la v0.2 porque necesitan analizar lo que se dice. Los umbrales son iniciales [VALIDAR] y se fijan solo con el conjunto de desarrollo (RD-05).

| ID | Dimensión | Métrica | Definición operativa | Unidad |
| --- | --- | --- | --- | --- |
| MD-01 | Presencia | Voz femenina presente | Al menos un hablante etiquetado como femenino con 10 s o más de habla | sí / no |
| MD-02 | Presencia | Voces por grupo | Número de hablantes con cada etiqueta | recuento |
| MD-03 | Presencia | Primera intervención femenina | Inicio del primer turno de una voz femenina | min:s |
| MD-04 | Participación | Cuota de tiempo | Segundos de habla del grupo ÷ segundos de voces etiquetadas (RN-04) | % |
| MD-05 | Participación | Cuota de turnos | Turnos del grupo ÷ total de turnos; las señales de escucha no cuentan como turno (D-14) | % |
| MD-06 | Participación | Turnos largos | Turnos de más de 30 s | recuento |
| MD-07 | Posición | Abre | Tiene el primer turno de más de 5 s del episodio | sí / no |
| MD-08 | Posición | Cierra | Tiene el último turno de más de 5 s | sí / no |
| MD-09 | Posición | Presenta | Retirada en la v0.2: necesita analizar lo que se dice | recuento |
| MD-10 | Conducción | Preguntas formuladas | Retirada en la v0.2: necesita analizar lo que se dice | recuento |
| MD-11 | Conducción | Cesiones de palabra | Retirada en la v0.2: necesita analizar lo que se dice | recuento |
| MD-12 | Reconocimiento | Preguntas recibidas | Retirada en la v0.2: necesita analizar lo que se dice | recuento |
| MD-13 | Reconocimiento | Presentada como experta | Retirada en la v0.2: necesita analizar lo que se dice | sí / no |
| MD-14 | Respeto del turno | Interrupciones recibidas y hechas | Solo los tipos «con éxito» e «intento» (RN-07) | recuento |
| MD-15 | Respeto del turno | Tasa de interrupción recibida | Interrupciones recibidas por cada 600 s de habla propia | por 10 min |
| MD-16 | Respeto del turno | Recupera la palabra | % de interrupciones con éxito tras las que vuelve a hablar en 10 s o menos | % |
| MD-17 | Respeto del turno | Apoyos recibidos | Señales de escucha que recibe mientras habla | por 10 min |

**Ratio de representación (RR).** Vale 1 cuando las voces femeninas hablan lo proporcional a cuántas son; por debajo de 1, hablan menos de lo que les correspondería.

```latex
RR = \frac{T_F / T_E}{N_F / N_E}
```

T\_F son los segundos de voces femeninas y T\_E los de todas las voces etiquetadas; N\_F es el número de voces femeninas y N\_E el de voces etiquetadas.

**Brecha de interrupción (BI).** Por encima de 1, se interrumpe más a las voces femeninas que a las masculinas, ya corregido por cuánto habla cada grupo.

```latex
BI = \frac{I_F / (T_F / 600)}{I_M / (T_M / 600)}
```

I son las interrupciones recibidas por cada grupo y T sus segundos de habla; 600 s son 10 minutos. Si un denominador es 0, se muestran las dos tasas y el índice como «no aplicable» (RN-13).

**Índice de protagonismo (IP), por persona, de 0 a 100.** Solo usa la voz: la v0.1 incluía conducción y reconocimiento, que necesitan palabras. Los pesos son una propuesta [VALIDAR] y se publican con su análisis de sensibilidad (11.3).

```latex
IP_i = 100 \cdot (0{,}5\,P_i + 0{,}25\,O_i + 0{,}25\,L_i)
```

- **P, participación:** cuota de tiempo de la persona ÷ cuota de quien más habla en el episodio.
- **O, posición:** (abre + cierra) ÷ 2.
- **L, turnos largos:** sus turnos de más de 30 s ÷ el máximo del episodio.
- Si el máximo de un componente es 0, ese componente vale 0 para todas las personas.

**Reglas de interrupción**

Un cambio de hablante de A a B es candidato si B empieza a hablar mientras A habla y se pisan más de 0,3 s. Las reglas solo miran tiempos, nunca lo que se dice.

| Tipo | Condición | ¿Cuenta como interrupción? |
| --- | --- | --- |
| Con éxito | A deja de hablar en los 2 s siguientes | Sí |
| Intento | A sigue hablando y B habla 1 s o más | Sí |
| Señal de escucha | B habla menos de 1 s y A sigue | No |

**Límite declarado:** sin palabras no se distinguen los solapamientos colaborativos (completar la frase de otra persona o reír a la vez), que pueden contarse como «intento». Cada caso se puede escuchar (RF-18).

## 7. Requisitos no funcionales

Cada requisito no funcional tiene un umbral y un método de medición. Los umbrales [VALIDAR] son propuestas que confirma la primera medición. Si no se alcanzan, se publica el valor real y se compensa con revisión humana; nunca se oculta.

| ID | Categoría | Requisito | Umbral | Cómo se mide | Prior. |
| --- | --- | --- | --- | --- | --- |
| RNF-01 | Rendimiento | Analizar un episodio de 60 min en GPU (la de Monica o la V100S) | 15 min o menos [VALIDAR el domingo 25] | Mediana de 3 audios cronometrados | Should |
| RNF-02 | Rendimiento | Mostrar un resultado precalculado | 2 s o menos | Medición en el navegador | Must |
| RNF-03 | Calidad | Acierto de la etiqueta de voz por hablante (M-02) | Exactitud equilibrada de 0,90 o más [VALIDAR] | Conjunto de prueba, con intervalo de confianza del 95 % | Must publicarlo; Should el umbral |
| RNF-04 | Calidad | Diarización (M-01) | DER del 20 % o menos [VALIDAR] | pyannote.metrics sobre el conjunto de prueba | Should |
| RNF-05 | Calidad | Detección de interrupciones (M-05) | F1 de 0,70 o más [VALIDAR] | Frente a la anotación de referencia, con tolerancia de ± 1 s | Should |
| RNF-06 | Equidad | Diferencia de error de voz entre grupos (M-03) | 5 puntos porcentuales o menos [VALIDAR] | Tasa de error por grupo con intervalo | Must publicarla |
| RNF-07 | Reproducibilidad | Instalar desde cero y regenerar la evaluación | 3 órdenes o menos; las tablas de 12.1 salen de un solo script | Prueba en máquina limpia por alguien ajeno al código | Must |
| RNF-08 | Agnosticismo | No aplica en la v0.2: el sistema no usa LLM | — | — | — |
| RNF-09 | Seguridad | Hallazgos abiertos en la versión entregada | 0 de gravedad alta | Informe de revisar\_seguridad.sh | Must |
| RNF-10 | Seguridad | Subida de archivos | Tipo real comprobado, límites de tamaño y duración, nombre generado por el sistema, FFmpeg sin shell y con tiempo máximo | Pruebas con archivos maliciosos y mal formados | Must |
| RNF-11 | Seguridad | No aplica en la v0.2: no hay LLM ni transcripción | — | — | — |
| RNF-12 | Privacidad | Lugar de tratamiento y retención | Tratamiento local, sin enviar el audio fuera; borrado según RF-23 | Inspección de configuración y prueba de borrado | Must |
| RNF-13 | Mantenibilidad | Cobertura de pruebas del módulo de análisis | 80 % de líneas o más [VALIDAR] | Informe de cobertura | Should |
| RNF-14 | Accesibilidad | WCAG 2.1 nivel AA en contraste, teclado y textos alternativos; el color nunca es la única señal | Sin errores de nivel AA | Revisión automática y recorrido solo con teclado | Should |
| RNF-15 | Usabilidad | Completar un análisis de ejemplo sin ayuda | 2 de 3 personas externas en menos de 3 min | Prueba con 3 personas ajenas al equipo | Should |
| RNF-16 | Robustez | Fallo de un paso del análisis | El análisis acaba en «error» con su motivo, nunca colgado | Prueba que simula fallos | Must |
| RNF-17 | Uso responsable | Consumo de la GPU | GPU solo para la diarización de audios largos | Registro de ejecuciones | Should |
| RNF-18 | Licencias | Compatibilidad de dependencias | Todas OSI o FSF y compatibles con la licencia del proyecto | listar\_licencias.sh | Must |
| RNF-19 | Idioma | Interfaz y demo en español en el MVP | — | Inspección | Must |
| RNF-20 | Portabilidad | Funcionar sin GPU | docker compose en CPU con pyannote y los ejemplos precalculados | Prueba en un portátil | Must |

Los umbrales de calidad (RNF-03 a RNF-06) se miden solo en el conjunto de prueba, siempre con su n y su intervalo de confianza.

## 8. Diseño funcional y UX

El recorrido tiene cuatro pantallas y un paso obligatorio: nadie ve los resultados de un audio nuevo sin haber confirmado antes las voces.

### 8.1 Flujo principal

[COMPLETAR diagrama: flujo principal · 2 carriles, 7 pasos]

El atajo discontinuo solo existe para los ejemplos precalculados, cuyas voces ya se confirmaron al prepararlos.

**Flujos alternativos**

- **Archivo no válido:** se rechaza en la subida con el motivo; no se crea análisis.
- **Falla un paso del análisis:** el análisis pasa a «error» con su motivo y se puede reintentar sin volver a subir el audio mientras dure la retención.
- **Ejemplo precalculado:** se salta la confirmación, porque ya se hizo al prepararlo, y se va directo a los resultados.

### 8.2 Pantallas

| Pantalla | Objetivo | Contenido mínimo | Estados que debe cubrir |
| --- | --- | --- | --- |
| Analizar | Empezar un análisis | Subida de archivo, lista de ejemplos, aviso de privacidad | Vacío, archivo no válido, subiendo, en cola |
| Confirmar voces | Fijar las etiquetas | Una tarjeta por hablante con 3 fragmentos, propuesta, confianza y tres opciones | Propuesta dudosa, todo confirmado |
| Resultados | Entender el episodio | Tarjetas de presencia e índices, línea de tiempo, gráfico por hablante, tabla de interrupciones con «escuchar» y, aparte, el tiempo de las voces cortas (D-15) | Sin voces femeninas, índice no aplicable |
| Cómo funciona | Confiar con criterio | Definiciones, fórmulas, exactitud por grupo y limitaciones | — |

### 8.3 Principios de experiencia de uso

| Principio | Regla concreta |
| --- | --- |
| Explicable | Cada número abre su fórmula y sus fragmentos (RN-06) |
| Incertidumbre visible | La confianza y «indeterminado» se muestran, nunca se esconden |
| Sin estereotipos | Paleta neutra, sin rosa ni azul; formas o etiquetas además del color (RNF-14) |
| Personas anónimas | «Hablante n» por defecto (RN-10); nunca hay rankings de personas |
| Lenguaje preciso | «Voz percibida como femenina», no «mujer»; «interrupción» solo para los tipos que cuentan |
| Describir, no juzgar | Los resultados describen el episodio, no califican a quien habla |

### 8.4 Textos clave

| Dónde | Texto |
| --- | --- |
| Antes de subir | «Analizaremos solo las voces de este audio, no lo que se dice. No identificamos a nadie y borramos el audio pasadas [COMPLETAR plazo de D-08]. Sube solo audios que tengas derecho a usar.» |
| Confirmar voces | «El sistema propone cómo suena cada voz; tú decides. Si sabes cómo se presenta públicamente esa persona, usa eso. Si no lo sabes, marca ‘indeterminado’.» |
| Resultados | «Estos datos describen este episodio, no a las personas. La voz percibida no es la identidad de género.» |
| Índice no aplicable | «En este episodio no hay voces de este grupo, así que el índice no se puede calcular.» |
| Error del análisis | «El análisis no ha podido terminar. Puedes reintentarlo sin volver a subir el audio durante [COMPLETAR plazo].» |

## 9. Integraciones

En ejecución, el sistema no depende de ningún servicio externo: separar voces y proponer la voz corren en infraestructura propia y el audio nunca sale de ella. Hugging Face solo interviene al instalar, para descargar el modelo de diarización.

### 9.1 Arquitectura

[COMPLETAR diagrama: arquitectura · todo el análisis en infraestructura propia]

Durante el análisis ninguna flecha sale de la infraestructura propia. Hugging Face solo interviene al instalar.

### 9.2 Integraciones externas

| Sistema | Para qué | Datos que salen | Autenticación | Límites conocidos | Si falla |
| --- | --- | --- | --- | --- | --- |
| Hugging Face Hub | Descargar una vez el modelo de diarización | Ninguno de las usuarias | Token de lectura y aceptar las condiciones del modelo | Acceso condicionado | Copia local en datos/modelos |
| GitHub, organización de la Comunidad | Código e integración continua | Código, sin datos | Cuentas del equipo | — | — |
| [Corpus AMI](https://groups.inf.ed.ac.uk/ami/corpus/) y [anotaciones de BUT](https://github.com/BUTSpeechFIT/AMI-diarization-setup) | Descargar los audios y las anotaciones de evaluación | Ninguno | Sin cuenta | Unos 30 MB por reunión | Repetir la descarga |

### 9.3 API interna (backend y web)

| Método y ruta | Para qué | Devuelve |
| --- | --- | --- |
| POST /analisis | Subir un audio o elegir un ejemplo | Identificador y estado |
| GET /analisis/{id} | Consultar estado y avance | Estado del contrato |
| GET /analisis/{id}/hablantes | Propuestas y muestras para confirmar | Lista de hablantes |
| POST /analisis/{id}/confirmacion | Enviar las etiquetas confirmadas | Estado actualizado |
| GET /analisis/{id}/resultado | Obtener los resultados | Resumen del episodio |
| GET /analisis/{id}/fragmento?inicio=&fin= | Escuchar un fragmento | Audio recortado, 15 s como máximo |
| GET /ejemplos | Listar episodios precalculados | Lista |
| GET /salud | Comprobar que el servicio responde | Estado |

El límite de 15 s del fragmento impide descargar el audio completo a través de la API. La descripción OpenAPI que publica FastAPI es la fuente de los tipos del frontend (RD-02): una ruta que no está en ella no existe.

### 9.4 Formato de intercambio

JSON según el contrato de datos, con el campo version\_contrato, tiempos en segundos con decimales y nombres de campo en español sin tildes.

## 10. Ética y cumplimiento

La ética se traduce en decisiones comprobables: cada principio tiene una medida de diseño, un requisito que la exige y una evidencia que el jurado puede revisar. Nada de esta sección es asesoramiento jurídico [VALIDAR con las mentoras de marco ético].

### 10.1 Principios operativos

Los siete requisitos de las Directrices éticas para una IA fiable, convertidos en medidas concretas:

| Requisito | Medida de diseño | Requisitos | Evidencia |
| --- | --- | --- | --- |
| Acción y supervisión humanas | Confirmación humana de cada etiqueta y modo manual | RN-02, RF-07, RF-08 | Demo y registro de quién etiquetó |
| Solidez técnica y seguridad | Evaluación con prueba ciega y revisión de seguridad | RNF-03 a RNF-05, RNF-09 y RNF-10 | Informes de evaluación y de seguridad |
| Privacidad y gestión de datos | Sin identificación, sin transcribir, retención corta y tratamiento local | RN-10, RF-23, RNF-12 | Prueba de borrado |
| Transparencia | Fórmulas visibles, fragmento por cifra, ficha del sistema | RN-06, RF-22 | Página «cómo funciona» |
| Diversidad, no discriminación y equidad | Error por grupo, categoría «indeterminado», comparación con lo proporcional | RN-03, RN-09, RNF-06 | Tabla de equidad |
| Bienestar social y ambiental | GPU solo para cargas pesadas | RNF-17 | Registro de uso |
| Rendición de cuentas | Código abierto, registro de decisiones, canal de reclamaciones en producción | RD-06, anexo C | Repositorio |

### 10.2 Perspectiva de género

- **La voz percibida no es la identidad de género.** La interfaz lo dice (8.4) y la referencia de evaluación es la autopresentación pública, no la percepción de quien anota (11.2). En AMI, la referencia es el sexo que el corpus registra en el código de cada participante.
- **No binario por diseño:** existe «indeterminado» y su tiempo se informa aparte (RN-03, RN-04).
- **Protagonismo, no solo minutos:** posición, turnos largos y respeto del turno (6.7).
- **Sesgo medido, no supuesto:** error por grupo con intervalo (RNF-06); por tipo de voz o acento, solo si hay etiquetas fiables [VALIDAR].
- **Interrupciones con matiz:** se separan las señales de escucha de las que quitan la palabra y se mide quién interrumpe a quién en todas las direcciones, sin presuponer el sentido. Sin palabras no se distinguen los solapamientos colaborativos: es un límite declarado (6.7).
- **Sin contenido:** el sistema no analiza lo que se dice, así que no puede asignar temas ni papeles por género.
- **Formación del reto:** aplicad y citad los materiales de la sesión de perspectiva de género [COMPLETAR].

### 10.3 Protección de datos (RGPD y LOPDGDD)

- La voz es un dato personal. Es dato biométrico de categoría especial solo si se trata para identificar de forma unívoca (art. 9), y el sistema no identifica.
- El sexo no es categoría especial, pero inferirlo exige exactitud (art. 5.1.d): por eso hay corrección humana.
- En producción, la base jurídica la fija la entidad responsable del tratamiento: interés legítimo con ponderación documentada (art. 6.1.f), o interés público o investigación con garantías (art. 89) [VALIDAR].
- Hay que informar a las personas cuya voz se analiza (arts. 13 y 14) y ofrecer una vía para ejercer sus derechos.
- Antes de producción: evaluación de impacto (art. 35) y contrato de encargo con el proveedor de nube (art. 28).

### 10.4 Propiedad intelectual

- **Analizar:** la excepción de minería de textos y datos de la Directiva (UE) 2019/790 (arts. 3 y 4), traspuesta en España por el Real Decreto-ley 24/2021, cubre el análisis salvo que el titular se haya reservado ese uso.
- **Mostrar no es analizar:** reproducir fragmentos en una demo pública es comunicarlos al público. En la demo, solo audios con licencia que lo permita o grabaciones propias con consentimiento.
- **Software, modelos y datos:** atribución del modelo de diarización (licencia CC-BY-4.0) y del corpus AMI (CC BY 4.0), condiciones de reutilización del Congreso [VALIDAR] e inventario de licencias en el README (RNF-18).

### 10.5 Ley de IA

El análisis está en la sección 4.3. De él salen RF-07, RF-08 y RN-02, y la obligación de documentar la evaluación del art. 6.4 si se invoca la excepción.

### 10.6 Usos permitidos y prohibidos

- **Permitidos:** auditoría agregada de contenidos, investigación, formación y sensibilización.
- **Prohibidos:** evaluar, puntuar o seleccionar a personas concretas (contratación, promoción, retribución); identificar a hablantes; inferir orientación sexual, identidad de género u otros atributos sensibles; vigilar a empleadas o empleados; publicar resultados por persona sin su consentimiento.

Una licencia OSI no puede restringir usos. Por eso esta política se aplica a la instancia que operemos y se recomienda en el README, pero no se añade a la licencia.

### 10.7 Riesgos éticos

Están en el registro de riesgos (4.2): R1 sesgo entre grupos, R2 clasificación legal, R11 generalizar en exceso y R12 atribuir un género erróneo.

## 11. Metodología

Trabajamos con el contrato de datos primero e integramos en puntos fijos. Evaluamos con anotación independiente, un conjunto de prueba que no se toca al ajustar, una línea base para comparar e intervalos de confianza.

### 11.1 Metodología de trabajo

1. **Contrato primero:** el contrato y los datos de ejemplo existen antes del código (sábado 24), así cada persona avanza sin esperar a las demás.
2. **Puntos de encuentro:** sábado a las 22:30; domingo a las 9:30, 14:00 y 21:00; de lunes a jueves, sin reuniones, cada una deja 3 líneas en el chat. Cada punto de encuentro actualiza los riesgos y el anexo C.
3. **Definición de preparado:** un requisito empieza a trabajarse solo si tiene criterio de aceptación, responsable y datos de prueba.
4. **Definición de hecho:** RD-10.
5. **Cambios de alcance:** se registran en el anexo C. Tras la congelación del martes 27, solo se corrigen errores.
6. **Agentes de IA:** escriben código y pruebas bajo revisión humana; nunca deciden reglas de negocio ni umbrales (RD-09).

### 11.2 Anotación de referencia

1. **Guía escrita antes de anotar:** qué es un turno, un solapamiento y cada tipo de interrupción, con ejemplos. Además de los tres tipos, se anota «colaborativo» para los solapamientos que no quitan la palabra (D-16).
2. **Anotación independiente:** A y C anotan los mismos clips por separado en Audacity; B no anota la prueba porque diseña las reglas.
3. **Acuerdo entre anotadoras:** kappa de Cohen para el tipo de interrupción (M-08). Si es menor de 0,6 [VALIDAR], se revisa la guía y se vuelve a anotar.
4. **Desacuerdos:** se resuelven por consenso, se registran y el resultado es la referencia.
5. **Etiqueta de voz de referencia:** la autopresentación pública de la persona. Si no consta, el caso se excluye de la métrica de voz y se cuenta aparte; la percepción de la anotadora nunca es la verdad. En AMI, la referencia es el sexo que el corpus registra en el código de cada participante (F o M).

### 11.3 Diseño de la evaluación

| Elemento | Decisión |
| --- | --- |
| Particiones | Desarrollo, para ajustar umbrales y pesos: reuniones IB4002 e IB4010 de AMI. Prueba, solo para medir, una vez por versión: EN2002a, EN2002c, ES2004a, IS1009a y TS3003a de AMI, y las grabaciones del equipo. Ninguna persona de prueba aparece en desarrollo (comprobado en las anotaciones) |
| Tamaño | 2 reuniones de desarrollo y 5 de prueba de AMI (fragmentos de 5 min en CPU; completas en GPU) y 2 grabaciones propias de 3 a 5 min. Con pocos datos, los resultados son orientativos y se presentan así |
| Unidad de análisis | Hablante para la voz, evento para las interrupciones, episodio para las métricas de tiempo |
| Líneas base | Voz: umbral de tono medio. Interrupciones: contar cualquier solapamiento. Diarización: sin línea base propia; se publica el DER con su intervalo |
| Ablación | Reglas de interrupción con la separación de voces de referencia de AMI frente a la de pyannote |
| Sensibilidad | Variar cada peso del índice ± 50 % e informar si cambia el orden de las personas |
| Incertidumbre | Intervalo de confianza del 95 % por remuestreo (bootstrap) y n siempre visible; sin contrastes de hipótesis cuando no hay datos suficientes |

### 11.4 Reproducibilidad

- Versiones fijadas en uv.lock y pnpm-lock.yaml; modelos con su versión.
- Las salidas de pyannote e inaSpeechSegmenter se guardan para regenerar la evaluación sin volver a procesar el audio.
- Semillas fijadas en todo lo que tenga azar.
- Un único script regenera las tablas de la sección 12.1 a partir de las etiquetas y las salidas guardadas.
- Registro de cada experimento: fecha, versión, partición y resultado.

### 11.5 Sesgos del propio proceso

| Sesgo | Control |
| --- | --- |
| Confirmación al ajustar las reglas | Prueba ciega; anota quien no diseña las reglas |
| Fuga de datos | Partición por hablante y por episodio |
| Grupos desequilibrados | Métricas equilibradas y desglosadas por grupo |
| Cambio de dominio, de reuniones en inglés grabadas con micrófonos de cabeza a conversaciones en español | Evaluar también con las grabaciones del equipo y mostrar la sesión del Congreso |
| Elegir episodios que salen bien | Las reuniones de AMI se eligieron por su composición de voces y su solapamiento, antes de ver resultados (plan definitivo, Parte 5.2) |

## 12. Métricas y cierre

El MVP se acepta si cumple los 15 requisitos Must, publica sus métricas de calidad con intervalo de confianza y entrega a tiempo los cuatro entregables del 30 de octubre.

### 12.1 Métricas de calidad del sistema

Los umbrales están en la sección 7; aquí se anotan los resultados medidos.

| ID | Métrica | Qué mide | Herramienta | Partición | Resultado (IC 95 %, n) |
| --- | --- | --- | --- | --- | --- |
| M-01 | DER, tasa de error de diarización | Errores en quién habla cuándo | pyannote.metrics | Prueba | [COMPLETAR] |
| M-02 | Exactitud equilibrada de la voz, por hablante | Acierto de la propuesta de voz | scikit-learn | Prueba | [COMPLETAR] |
| M-03 | Error por grupo y diferencia entre grupos | Equidad del clasificador | Script propio | Prueba | [COMPLETAR] |
| M-04 | Error absoluto del % de tiempo femenino | Precisión de la métrica principal | Script propio | Prueba | [COMPLETAR] puntos |
| M-05 | Precisión, exhaustividad y F1 de interrupciones (± 1 s) | Detección de interrupciones | Script propio | Prueba | [COMPLETAR] |
| M-06 | Retirada en la v0.2: no hay juez LLM | — | — | — | — |
| M-07 | Retirada en la v0.2: no hay juez LLM | — | — | — | — |
| M-08 | Kappa entre anotadoras | Fiabilidad de la referencia | Script propio | Prueba | [COMPLETAR] |
| M-09 | Minutos de proceso por hora de audio | Rendimiento | Cronómetro | 3 audios completos | [COMPLETAR] |

### 12.2 Métricas del proyecto

| Métrica | Objetivo |
| --- | --- |
| Requisitos Must verificados | 15 de 15 |
| Hallazgos de seguridad de gravedad alta abiertos | 0 |
| Pruebas e integración continua en la versión entregada | En verde |
| Entregables en plazo | 4 de 4, más la versión corta |
| Decisiones [DECIDIR] abiertas al cierre | 0 |

### 12.3 Criterios de aceptación del MVP

- [ ] Los 15 RF Must, verificados con su método.
- [ ] Los RNF Must, cumplidos; los Should, medidos y publicados aunque no alcancen el umbral.
- [ ] Evaluación en la partición de prueba con intervalo de confianza y tabla de equidad.
- [ ] Recorrido completo demostrado con un audio nuevo y con un ejemplo.
- [ ] Instalación reproducida por alguien ajeno al código.
- [ ] Ni audios, ni transcripciones, ni nombres, ni claves en el historial del repositorio.
- [ ] Anexo C sin decisiones abiertas.

### 12.4 Entregables y plazos

| Entregable | Plazo | Resp. | Estado |
| --- | --- | --- | --- |
| Repositorio público con licencia OSI o FSF | Antes de las 08:00 del Oct 30, 2026 | B | Pendiente |
| README con descripción, instalación y uso, terceros y sus licencias, y hoja de ruta | Antes de las 08:00 del Oct 30, 2026 | A | Pendiente |
| Presentación .pptx de 20 diapositivas como máximo | Antes de las 08:00 del Oct 30, 2026 | C | Pendiente |
| Vídeo explicativo de 5 minutos | Antes de las 08:00 del Oct 30, 2026 | C | Pendiente |
| Versión corta de la presentación: 5 minutos con demo | Antes del evento del Nov 4, 2026 | C | Pendiente |

Si falta cualquier entregable en plazo, el equipo queda fuera de la evaluación.

### 12.5 Cierre

**Aprobación de la versión 1.0**

| Nombre | Rol | Fecha | Conforme |
| --- | --- | --- | --- |
| [COMPLETAR] | Persona A | [COMPLETAR] | [COMPLETAR] |
| [COMPLETAR] | Persona B | [COMPLETAR] | [COMPLETAR] |
| [COMPLETAR] | Persona C | [COMPLETAR] | [COMPLETAR] |

**Tras la entrega**

- [ ] Retrospectiva de 30 minutos: qué funcionó, qué no y qué cambiaríamos; se añade al CHANGELOG.
- [ ] Traspaso: hoja de ruta en el README, incidencias abiertas etiquetadas y decisiones pendientes para producción.
- [ ] Archivo: versión 1.0 de este documento exportada a docs/01-funcional.md.

## Anexos

### A. Glosario

| Término | Definición |
| --- | --- |
| Ablación | Comparar el sistema con y sin una pieza para medir lo que aporta |
| AMI | Corpus abierto de reuniones de trabajo grabadas y anotadas (quién habla cuándo), con licencia CC BY 4.0 |
| Bootstrap | Remuestreo repetido de los datos para estimar un intervalo de confianza con muestras pequeñas |
| DER | Proporción de tiempo mal atribuido: habla no detectada, falsas alarmas y confusión de hablante |
| Diarización | Saber quién habla y cuándo dentro de un audio, sin identificar a nadie |
| Exactitud equilibrada | Media del acierto de cada clase; no se infla cuando un grupo es mayoritario |
| F1 | Equilibrio entre precisión (cuántas detecciones son ciertas) y exhaustividad (cuántos casos reales se detectan) |
| Juez LLM | Retirado en la v0.2: el sistema no usa LLM |
| Kappa de Cohen | Acuerdo entre dos clasificaciones descontando el debido al azar; 1 es acuerdo total |
| Línea base | Método sencillo de referencia; sin ella un resultado no se puede interpretar |
| MoSCoW | Prioridad Must, Should, Could, Won't |
| Partición de desarrollo / de prueba | Datos para ajustar / datos que solo sirven para medir |
| Señal de escucha | Intervención breve («ajá», «claro») que acompaña sin pedir el turno |
| Solapamiento | Momento en que dos personas hablan a la vez |

### B. Matriz de trazabilidad

Cada criterio de evaluación tiene requisitos que lo cubren y una evidencia que el jurado puede ver. Una fila sin evidencia es un punto perdido.

| Criterio | Peso | Requisitos y reglas | Evidencia |
| --- | --- | --- | --- |
| Calidad técnica | 30 % | RF-05 a RF-07, RF-12 a RF-14, RF-16, RNF-01 a RNF-05, RNF-07, RNF-13 | Informe de evaluación, integración continua, demo |
| Perspectiva de género | 10 % | RN-02 a RN-04, RN-09, RF-07, RF-16, RNF-06 | Sección 10.2 y tabla de equidad |
| Código abierto | 10 % | RD-01 a RD-04, RNF-07, RNF-18 | README, licencias, CONTRIBUTING |
| Ética y normativa | 5 % | RF-07, RF-08, RF-23, RNF-12; secciones 4.3 y 10 | Secciones 4.3 y 10 de este documento y docs/ficha\_del\_sistema.md |
| Plan de despliegue | 5 % | Sección 9 y plan de producción | docs/plan\_produccion.md |
| Impacto | 15 % | Sección 2.1 | Hallazgos en las reuniones de AMI, las grabaciones del equipo y la sesión del Congreso |
| Innovación | 15 % | Catálogo 6.7, RF-14, RF-16 | Protagonismo medido solo con la voz, confirmación humana y ablación |
| Comunicación | 10 % | RF-17, RF-18, RF-22, RNF-15 | Presentación, vídeo y demo |
| Bases: IA como elemento relevante | Requisito | RF-05, RF-06 | Sección 9.1 |
| Bases: LLM agnóstico y modelos abiertos | Requisito | No aplica: el sistema no usa LLM | — |
| Bases: repositorio público con licencia | Requisito | C2, RNF-18 | Repositorio |

### C. Registro de decisiones

| ID | Decisión | Opción A | Opción B | Criterio para elegir | Estado | Fecha |
| --- | --- | --- | --- | --- | --- | --- |
| D-01 | Gestor del backend | uv | — | Norma del equipo | Decidida | 22 oct 2026 |
| D-02 | Frontend | React, Vite y TypeScript con pnpm | Streamlit | Demo más cuidada y trabajo de C independiente del backend | Decidida | 23 oct 2026 |
| D-03 | Motor de la propuesta de voz | Modelo preentrenado: inaSpeechSegmenter, con el tono medio como línea base | Clasificador propio entrenado | Elegida A: no requiere entrenar y cabe en las horas disponibles; su acierto por grupo se mide (M-02, M-03) | Decidida | 24 oct 2026 |
| D-04 | Modo de etiquetado por defecto | Asistido | Manual | Elegida A en el MVP, con confirmación humana siempre; B por defecto en producción hasta tener la evaluación legal (4.3) | Decidida | 24 oct 2026 |
| D-05 | Trazas del LLM | Langfuse autoalojado | Sin trazas | Elegida B: el sistema no usa LLM | Decidida | 24 oct 2026 |
| D-06 | Licencia del proyecto | Apache-2.0 | MIT | Reconocida por OSI y FSF, compatible con las dependencias y con protección de patentes | Propuesta | — |
| D-07 | Modelos de OVHcloud | Agentes de programación: Qwen3.8-27B | — | La aplicación no usa LLM. Licencia Apache 2.0; nombre exacto del modelo, sin modelos virtuales; ni Mistral (OVHcloud lo retira el 4 nov 2026) ni Llama (licencia no abierta) | Decidida | 24 oct 2026 |
| D-08 | Retención del audio y subidas en la demo pública | [COMPLETAR, p. ej. 24 h] | Borrar al terminar el análisis | Poder escuchar fragmentos frente a minimizar datos | Abierta | — |
| D-09 | Umbrales iniciales | Valores de 6.7 | — | Se fijan con la partición de desarrollo | Propuesta | — |
| D-10 | Qué analiza el sistema | Solo la voz | Voz y transcripción | Elegida A: privacidad (no se procesa el contenido y el audio no sale), menos horas y menos piezas | Decidida | 24 oct 2026 |
| D-11 | Datos | Grabaciones propias, corpus AMI y una sesión del Congreso | Episodio de podcast público anotado a mano | Elegida A: AMI ya está anotado y tiene licencia CC BY 4.0; las grabaciones propias se pueden enseñar | Decidida | 24 oct 2026 |
| D-12 | Nombre del proyecto | athenis-voces | Tiempo de Voz | Decisión del equipo | Decidida | 24 oct 2026 |
| D-13 | Nombre y género de las etiquetas de voz (RN-03) | femenino, masculino e indeterminado | femenina, masculina y no determinada | Decisión de Monica Gomez | Decidida | 24 oct 2026 |
| D-14 | Señales de escucha y cuota de turnos (MD-05) | No cuentan como turno | Sí cuentan como turno | Un «ajá» no debe hacer que alguien parezca participar más | Decidida | 24 oct 2026 |
| D-15 | Voces de menos de 10 s (RN-01) | No cuentan como voz ni se confirman; su tiempo se muestra aparte | Quitar el mínimo de 10 s | Evitar voces falsas por ruidos sin esconder a nadie que hable poco | Decidida | 24 oct 2026 |
| D-16 | Qué se anota como interrupción en la referencia (11.2) | Criterio humano al escuchar, con una cuarta etiqueta solo para anotar: «colaborativo», que no cuenta | Solo las reglas de tiempo | Con solo reglas de tiempo la referencia sería el propio código y la línea base «contar cualquier solapamiento» no tendría sentido; así el límite declarado de 6.7 se ve en los resultados | Decidida | 24 oct 2026 |
| D-17 | Audio con menos de dos voces presentes (RNF-16) | El análisis acaba en «error» con un motivo claro: «solo se ha detectado una voz que se pueda confirmar» | Dar un resultado con los índices «no aplicable» | Con una sola voz no hay nada que comparar; el motivo explica por qué no hay resultado, en vez de descartar el audio en silencio | Decidida | 25 oct 2026 |
| D-18 | Voz de 10 s o más sin 3 tramos de 3 s sin solapamiento (RN-01) | No es voz presente: no se confirma y su tiempo cuenta como voz corta (D-15) | Descartarla sin contar su tiempo | Sin esos tramos no se puede escuchar para confirmarla, pero tampoco se puede esconder a alguien que sí habló | Decidida | 25 oct 2026 |

### D. Plantilla para añadir un requisito

```markdown
**RF-XX — [nombre corto]**
- Descripción: El sistema debe …
- Prioridad: Must | Should | Could | Won't
- Origen: B | R | E
- Criterio de aceptación: Dado …, cuando …, entonces … (medible)
- Verificación: P | D | I | A
- Responsable: A | B | C
- Depende de: …
- Trazabilidad: criterio de la rúbrica …
```

### Fuentes

- Bases del reto «Mujeres por la IA Abierta» (documento de la organización).
- [AMI Meeting Corpus: descripción y licencia CC BY 4.0](https://groups.inf.ed.ac.uk/ami/corpus/)
- [AMI: códigos de participante, cuya primera letra indica F o M](https://groups.inf.ed.ac.uk/ami/corpus/participantids.shtml)
- [BUT: anotaciones de AMI para separar voces (Apache 2.0)](https://github.com/BUTSpeechFIT/AMI-diarization-setup)
- [Congreso de los Diputados: aviso legal y condiciones de reutilización](https://www.congreso.es/en/cem/aviso-legal)
