# Research: Análisis y evaluación

**Rama**: `002-analisis` | **Fecha**: 2026-10-25

No quedan elementos NEEDS CLARIFICATION. Las fórmulas las fija el catálogo 6.7 del funcional y los
umbrales son valores iniciales de `config.py`, ajustables solo con la partición de desarrollo (RD-05).

---

## Decisión 1: Todo el análisis se calcula con tiempos

**Elegido**: el análisis solo usa los turnos, los solapamientos y las etiquetas confirmadas. Es código
normal, sin modelos y sin LLM.

**Justificación**: es lo que pide D-10 y la constitución (punto 6). Además, así cada cifra se puede
comprobar a mano con un caso inventado (SC-001) y siempre da lo mismo con los mismos datos.

**Alternativas descartadas**:
- Clasificar las interrupciones por lo que se dice: prohibido (no se transcribe). El límite queda
  declarado: los solapamientos colaborativos pueden contarse como «intento» (6.7).

---

## Decisión 2: Un solo sitio para los umbrales

**Elegido**: todos los umbrales y pesos (10 s, 5 s, 30 s, 0,3 s, 2 s, 1 s, 10 s de recuperación y los
pesos del IP) viven en `config.py`, en un `dataclass` inmutable. Cada función los recibe como
parámetro con `CONFIG` por defecto.

**Justificación**: FR-012 y RD-05. Se puede probar con otros valores sin tocar el código, y el
nombre de cada umbral dice cómo se compara («mas_de» es estricto, «desde» es mayor o igual).

**Alternativas descartadas**:
- Constantes dentro de cada módulo: obligaría a buscar cada umbral al ajustarlo.

---

## Decisión 3: «No aplicable» es `None`, nunca 0

**Elegido**: si el denominador de un índice o de una tasa es 0, el valor es `None` y el índice sigue
mostrando su fórmula (RN-13, FR-009).

**Justificación**: un 0 diría «no hay brecha», que es falso cuando simplemente no se puede calcular
(por ejemplo, TS3003a no tiene voces femeninas). SC-003 lo cubre con una prueba.

---

## Decisión 4: Señales de escucha fuera del recuento de turnos

**Elegido**: antes de contar turnos, se quitan los turnos de quien emite una señal de escucha (D-14).
Sus segundos sí cuentan como tiempo de habla.

**Justificación**: aclaración 2 de la spec. Un «ajá» no debe hacer que alguien parezca participar más.

---

## Decisión 5: Métricas de evaluación

**Elegido**:
- DER (M-01): `pyannote-metrics`, del grupo opcional `evaluacion`.
- F1 de interrupciones (M-05): emparejamiento uno a uno, de los instantes más cercanos a los más
  lejanos, con tolerancia de ± 1 s.
- Kappa de Cohen (M-08): propia. Empareja los eventos de A y C (± 1 s) y compara el tipo que puso cada una; si solo una marcó un evento, la otra cuenta como «ninguno».
- Intervalos de confianza: bootstrap con semilla fija (1000 remuestreos), remuestreando reuniones
  enteras y no filas sueltas.

**Justificación**: pyannote-metrics es la implementación de referencia del DER. El resto son pocas
líneas y se prueban a mano. La semilla fija hace que la tabla sea reproducible (11.4, RNF-07).

**Alternativas descartadas**:
- scikit-learn para la kappa: una dependencia pesada para una fórmula de cinco líneas.

---

## Decisión 6: Confirmación ideal al evaluar con AMI

**Elegido**: AMI no tiene una persona que confirme las voces. Para M-04 y la ablación, `evaluar.py`
asigna a cada voz de pyannote el sexo que AMI indica para quien más se solapa con ella
(`resultado_ideal`). Es una confirmación perfecta, y así se mide solo el análisis, no la propuesta.

**Justificación**: aísla el error de la separación de voces del error de la propuesta (11.3).

**Límite declarado**: la cifra es un mejor caso. Se explica en el informe.

---

## Decisión 7: La evaluación no vuelve a procesar el audio

**Elegido**: `evaluar.py` lee `.rttm` y `.json` ya guardados y las etiquetas de Audacity. Lo que
falta no se evalúa y no cuenta en n.

**Justificación**: FR-015 y SC-008. Una persona ajena al código regenera la tabla en minutos, sin GPU.
