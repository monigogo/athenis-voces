# Datos de evaluación

Qué datos usamos para medir el sistema, de dónde salen, con qué licencia y cómo se citan (tarea
A09; funcional, secciones 4.4 y 11). **Ningún audio entra en el repositorio** (RD-04, constitución
regla 7): todo vive en `datos/`, que está en `.gitignore`.

## Cómo se descargan

Desde la raíz del repositorio:

```bash
scripts/descargar_datos.sh
```

Baja las 7 reuniones de AMI a `datos/ami/audios/` y las anotaciones de BUT a
`datos/ami/anotaciones_but/`. Comprueba la huella SHA-256 de cada audio (`scripts/ami.sha256`) y
fija las anotaciones a un commit concreto. Si algo no cuadra, no lo guarda y avisa. Se puede repetir:
lo que ya está bien no se vuelve a bajar. Ocupa unos 430 MB.

## Fuentes

| Fuente | Qué es | Licencia | Dónde queda | ¿Al repositorio? |
| --- | --- | --- | --- | --- |
| [Corpus AMI](https://groups.inf.ed.ac.uk/ami/corpus/) | Audio de reuniones en inglés, mezcla de los micrófonos de cabeza (`Mix-Headset`), WAV mono a 16 kHz | [CC BY 4.0](https://groups.inf.ed.ac.uk/ami/corpus/license.shtml) | `datos/ami/audios/` | No |
| [Anotaciones de BUT](https://github.com/BUTSpeechFIT/AMI-diarization-setup) | Quién habla y cuándo en cada reunión (RTTM), sacado de las anotaciones manuales de AMI 1.6.2. Usamos `only_words` | Apache-2.0 | `datos/ami/anotaciones_but/`, commit `2509d89` | No |
| Grabaciones propias del equipo | 2 conversaciones en español, de 3 a 5 min, con consentimiento por escrito | Solo para este reto | Ordenadores del equipo | No |
| Sesión del Congreso | Una sesión pública, para la demo | Reutilización citando la fuente [VALIDAR] | `datos/`, en local | No |

Las etiquetas de interrupciones que anotan A y C sí entran en el repositorio, en
`evaluacion/etiquetas/`: no llevan audio, ni texto, ni nombres.

## Reuniones de AMI y para qué se usan

| Partición | Reuniones | Para qué |
| --- | --- | --- |
| Desarrollo | IB4002, IB4010 | Ajustar umbrales y pesos |
| Prueba | EN2002a, EN2002c, ES2004a, IS1009a, TS3003a | **Solo para medir**, una vez por versión; nada se ajusta con ellas (constitución, regla 9) |

Ninguna persona de prueba aparece en desarrollo (funcional, 11.3). En AMI, la referencia de la voz es
el sexo que el corpus registra en la primera letra del código de cada participante, F o M
(funcional, 11.2).

## Cómo citar

- **Corpus AMI:** J. Carletta, S. Ashby, S. Bourban, M. Flynn, M. Guillemot, T. Hain, J. Kadlec,
  V. Karaiskos, W. Kraaij, M. Kronenthal, et al. *The AMI meeting corpus: A pre-announcement.* En:
  International Workshop on Machine Learning for Multimodal Interaction, Springer, 2006, pp. 28–39.
- **Anotaciones de BUT:** F. Landini, J. Profant, M. Diez, L. Burget. [*Bayesian HMM clustering of
  x-vector sequences (VBx) in speaker diarization: theory, implementation and analysis on standard
  tasks*](https://www.sciencedirect.com/science/article/pii/S0885230821000619).
