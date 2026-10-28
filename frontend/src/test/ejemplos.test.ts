/// <reference types="vite/client" />
/**
 * Pruebas de los ejemplos precalculados (RF-02).
 *
 * Los datos son los mismos JSON que sirve el backend en GET /ejemplos (backend/ejemplos): la web los
 * muestra aunque no haya servidor, y con servidor pide cada uno por su id.
 */

import { describe, expect, it } from "vitest";
import { LISTA_EJEMPLOS } from "../data/ejemplos";
import type { Resultado } from "../types/contrato";

const DEL_BACKEND = Object.values(
  import.meta.glob<Resultado>("../../../backend/ejemplos/*.json", {
    eager: true,
    import: "default",
  }),
);

describe("ejemplos precalculados (RF-02)", () => {
  it("son las reuniones IB4002 e IB4010 del corpus AMI", () => {
    expect(LISTA_EJEMPLOS.map((e) => e.id)).toEqual(["IB4002", "IB4010"]);
  });

  it("cada id es el id_analisis de un JSON de backend/ejemplos (POST /analisis con ejemplo=<id>)", () => {
    const ids = LISTA_EJEMPLOS.map((e) => e.id).sort();
    expect(ids).toEqual(DEL_BACKEND.map((r) => r.id_analisis).sort());
    for (const ej of LISTA_EJEMPLOS) {
      expect(ej.resultado.id_analisis).toBe(ej.id);
    }
  });

  it("sin servidor muestran los mismos datos que el backend", () => {
    for (const ej of LISTA_EJEMPLOS) {
      expect(ej.resultado).toEqual(DEL_BACKEND.find((r) => r.id_analisis === ej.id));
    }
  });

  it("la duración y las voces salen del resultado", () => {
    for (const ej of LISTA_EJEMPLOS) {
      expect(ej.duracion).toBe(ej.resultado.duracion);
      expect(ej.voces_femeninas).toBe(ej.resultado.voz_femenina_presente);
      expect(ej.total_hablantes).toBe(ej.resultado.hablantes.length);
    }
  });

  it("dicen de dónde salen, que nadie confirmó las voces y que no hay audio", () => {
    for (const ej of LISTA_EJEMPLOS) {
      expect(ej.origen).toContain(`reunión ${ej.id}`);
      expect(ej.origen).toContain("corpus AMI");
      expect(ej.origen).toContain("CC BY 4.0");
      expect(ej.origen).toContain("https://groups.inf.ed.ac.uk/ami/corpus/");
      expect(ej.descripcion).toContain("propuestas por el modelo, sin confirmación humana");
      expect(ej.descripcion).toContain("sin audio");
    }
  });
});
