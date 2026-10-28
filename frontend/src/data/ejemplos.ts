/**
 * Ejemplos precalculados (RF-02).
 *
 * Son los mismos JSON que sirve el backend en GET /ejemplos (backend/ejemplos), importados tal cual:
 * la web los muestra aunque no haya servidor y no hay una segunda copia que se desfase.
 */

import IB4002 from "../../../backend/ejemplos/IB4002.json";
import IB4010 from "../../../backend/ejemplos/IB4010.json";
import type { EjemploPrecalculado, Resultado } from "../types/contrato";

function ejemplo(resultado: Resultado): EjemploPrecalculado {
  const id = resultado.id_analisis;
  return {
    id,
    nombre: `Reunión ${id} del corpus AMI`,
    descripcion:
      "Etiquetas de voz propuestas por el modelo, sin confirmación humana (solo evaluación); sin audio.",
    origen: `Resultado del sistema sobre la reunión ${id} del corpus AMI (CC BY 4.0, https://groups.inf.ed.ac.uk/ami/corpus/)`,
    duracion: resultado.duracion,
    voces_femeninas: resultado.voz_femenina_presente,
    total_hablantes: resultado.hablantes.length,
    resultado,
  };
}

export const LISTA_EJEMPLOS: EjemploPrecalculado[] = [
  ejemplo(IB4002 as Resultado),
  ejemplo(IB4010 as Resultado),
];
