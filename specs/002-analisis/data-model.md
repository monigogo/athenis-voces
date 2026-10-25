# Modelo de datos: Análisis y evaluación

**Rama**: `002-analisis` | **Fecha**: 2026-10-25

Esta feature no define campos propios: lee `EntradaAnalisis` y rellena `Resultado`, tal como los fija
[docs/contrato_de_datos.md](../../docs/contrato_de_datos.md) y `backend/src/contrato.py`. Aquí solo
se explica cómo se calcula cada cosa.

---

## Entrada

`EntradaAnalisis`: duración, turnos, solapamientos y una etiqueta confirmada por voz
(`femenino`, `masculino` o `indeterminado`, con su origen). Solo hay entrada cuando todas las voces
presentes están confirmadas.

## Cálculo de las cifras

| Cifra | Cálculo | Módulo | Requisito |
|-------|---------|--------|-----------|
| Tiempo de habla | Suma de sus turnos; un solapamiento cuenta entero para cada persona | `participacion.py` | MD-04 |
| Turnos | Sus turnos sin las señales de escucha | `participacion.py` | MD-05, D-14 |
| Turnos largos | Turnos de más de 30 s | `participacion.py` | MD-06 |
| Voz femenina presente | Alguna voz femenina con 10 s o más de habla | `participacion.py` | MD-01, RN-01 |
| Primera intervención femenina | Inicio del primer turno de una voz femenina | `participacion.py` | MD-03 |
| Voces cortas | Segundos de las voces que no llegan a presentes | `participacion.py` | FR-018, D-15 |
| Abre | Autor del primer turno de más de 5 s | `posicion.py` | MD-07 |
| Cierra | Autor del último turno de más de 5 s | `posicion.py` | MD-08 |
| Candidato | B empieza mientras A habla y se pisan más de 0,3 s | `interrupciones.py` | FR-003 |
| Con éxito | A deja de hablar en los 2 s siguientes al inicio de B | `interrupciones.py` | FR-004 |
| Intento | A sigue y B habla 1 s o más | `interrupciones.py` | FR-004 |
| Señal de escucha | A sigue y B habla menos de 1 s | `interrupciones.py` | FR-004 |
| Tasa recibida | Interrupciones recibidas por cada 10 min de habla propia | `interrupciones.py` | MD-15, RN-08 |
| Recupera la palabra | % de «con éxito» tras los que la persona vuelve a hablar en 10 s o menos | `interrupciones.py` | MD-16 |
| RR | (T_F / T_E) ÷ (N_F / N_E) | `indices.py` | FR-007 |
| BI | (I_F / (T_F / 600)) ÷ (I_M / (T_M / 600)) | `indices.py` | FR-007 |
| IP | 100 · (0,5 P + 0,25 O + 0,25 L) | `indices.py` | FR-008 |

Solo «con éxito» e «intento» cuentan como interrupción (RN-07).

## Reglas

- **No aplicable**: si el denominador es 0, el valor es `None` y se muestra la fórmula (RN-13).
- **Indeterminado**: no entra en los denominadores de grupo y se informa aparte (RN-03, RN-04).
- **Fórmula y tiempos**: cada índice lleva su fórmula y cada interrupción su inicio y su fin (RN-06).
- **Sin voces femeninas o sin masculinas**: RR y BI valen «no aplicable» (TS3003a, IS1009a).

## Evaluación

| Entidad | Campos | Origen |
|---------|--------|--------|
| `Reunion` | nombre, DER (M-01), error del % femenino (M-04), ablación, si la confirmación fue ideal y, por voz, el sexo en AMI y la propuesta del modelo (M-02, M-03) | `evaluacion/evaluar.py` |
| `Grabacion` | nombre, detección del sistema (M-05), línea base y kappa (M-08) | `evaluacion/evaluar.py` |
| `Deteccion` | verdaderos, falsos, precisión, exhaustividad, F1 | `evaluacion/metricas.py` |
| `Der` | segundos con error y segundos de voz (el DER es su cociente) | `evaluacion/metricas.py` |
| Tiempo | duración del audio y segundos del proceso, en `<audio>.tiempo.json` (M-09) | `evaluacion/cronometrar.py` |

Cada resultado indica su n (episodios y minutos) y su intervalo de confianza del 95 % por bootstrap
(FR-017).
