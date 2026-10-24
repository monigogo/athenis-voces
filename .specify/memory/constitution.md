# Constitución de athenis-voces

1. Manda el documento funcional: no se construye nada que no esté en docs/01-funcional.md.
2. TDD obligatorio: ninguna tarea de código empieza sin su prueba escrita antes y fallando.
3. Un solo contrato de datos: docs/contrato_de_datos.md y sus JSON. Cambiarlo exige el acuerdo de las tres.
4. Todo gratuito y de código abierto, salvo los servicios que cede el reto (OVHcloud).
5. uv solo en backend/; pnpm solo en frontend/.
6. El sistema analiza la voz, nunca lo que se dice: no se transcribe.
7. No entran en el repositorio audios, transcripciones, nombres reales ni claves (RD-04).
   Los audios de evaluación se descargan con scripts/descargar_datos.sh.
8. Una persona confirma cada voz, con tres opciones: femenina, masculina y no determinada.
9. Las reuniones de prueba solo sirven para medir; nada se ajusta con ellas.
10. Primero los requisitos Must; los demás, solo si sobra tiempo.
11. Cada feature recorre las 8 fases y ninguna fase empieza sin el fichero de la anterior.
