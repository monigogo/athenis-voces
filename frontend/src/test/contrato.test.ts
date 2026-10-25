import { describe, expect, it } from "vitest";
import {
  EJEMPLO_CON_VOCES_FEMENINAS,
  EJEMPLO_MUCHAS_INTERRUPCIONES,
  EJEMPLO_SIN_VOCES_FEMENINAS,
  LISTA_EJEMPLOS,
} from "../data/ejemplos";
import { VERSION_CONTRATO, esPropuestaDudosa, formatearSegundos } from "../types/contrato";

describe("Contrato de datos de Athenis Voces (v0.2)", () => {
  it("todos los ejemplos tienen versión de contrato '0.2'", () => {
    expect(EJEMPLO_CON_VOCES_FEMENINAS.version_contrato).toBe(VERSION_CONTRATO);
    expect(EJEMPLO_SIN_VOCES_FEMENINAS.version_contrato).toBe(VERSION_CONTRATO);
    expect(EJEMPLO_MUCHAS_INTERRUPCIONES.version_contrato).toBe(VERSION_CONTRATO);
  });

  it("los hablantes están numerados desde 1 (RN-10)", () => {
    for (const ej of [
      EJEMPLO_CON_VOCES_FEMENINAS,
      EJEMPLO_SIN_VOCES_FEMENINAS,
      EJEMPLO_MUCHAS_INTERRUPCIONES,
    ]) {
      for (const h of ej.hablantes) {
        expect(h.hablante).toBeGreaterThanOrEqual(1);
      }
      for (const t of ej.turnos) {
        expect(t.hablante).toBeGreaterThanOrEqual(1);
      }
    }
  });

  it("sin voces femeninas: los índices tienen valor null ('no aplicable', RN-13)", () => {
    expect(EJEMPLO_SIN_VOCES_FEMENINAS.voz_femenina_presente).toBe(false);
    expect(EJEMPLO_SIN_VOCES_FEMENINAS.primera_intervencion_femenina).toBeNull();

    for (const indice of EJEMPLO_SIN_VOCES_FEMENINAS.indices) {
      expect(indice.valor).toBeNull();
    }
  });

  it("con voces femeninas: índices válidos y presencia registrada", () => {
    expect(EJEMPLO_CON_VOCES_FEMENINAS.voz_femenina_presente).toBe(true);
    expect(EJEMPLO_CON_VOCES_FEMENINAS.primera_intervencion_femenina).not.toBeNull();

    const rr = EJEMPLO_CON_VOCES_FEMENINAS.indices.find((i) => i.nombre === "ratio_representacion");
    expect(rr?.valor).toBeGreaterThan(0);
  });

  it("identifica propuestas dudosas entre 0.35 y 0.65 (RF-06)", () => {
    expect(esPropuestaDudosa({ etiqueta: "femenino", confianza: 0.5 })).toBe(true);
    expect(esPropuestaDudosa({ etiqueta: "masculino", confianza: 0.35 })).toBe(true);
    expect(esPropuestaDudosa({ etiqueta: "femenino", confianza: 0.65 })).toBe(true);
    expect(esPropuestaDudosa({ etiqueta: "femenino", confianza: 0.85 })).toBe(false);
    expect(esPropuestaDudosa({ etiqueta: "masculino", confianza: 0.2 })).toBe(false);
    expect(esPropuestaDudosa(null)).toBe(false);
  });

  it("formatearSegundos formatea correctamente o devuelve 'no aplicable'", () => {
    expect(formatearSegundos(null)).toBe("no aplicable");
    expect(formatearSegundos(undefined)).toBe("no aplicable");
    expect(formatearSegundos(180)).toBe("3m 00s");
    expect(formatearSegundos(42.5)).toBe("42.5s");
  });

  it("hay exactamente 3 ejemplos precalculados en la lista (RF-02)", () => {
    expect(LISTA_EJEMPLOS.length).toBe(3);
  });
});
