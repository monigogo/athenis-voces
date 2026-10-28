import { describe, expect, expectTypeOf, it } from "vitest";
import { LISTA_EJEMPLOS } from "../data/ejemplos";
import { EJEMPLO_CON_VOCES_FEMENINAS, EJEMPLO_SIN_VOCES_FEMENINAS } from "../data/simulacion";
import type { components } from "../types/api";
import {
  type Completo,
  type Confirmacion,
  type EstadoAnalisis,
  type Hablante,
  type HablantesParaConfirmar,
  type MetricasHablante,
  type PropuestaVoz,
  type Resultado,
  VERSION_CONTRATO,
  esPropuestaDudosa,
  formatearSegundos,
} from "../types/contrato";

type Esquemas = components["schemas"];

const RESULTADOS: Resultado[] = [
  EJEMPLO_CON_VOCES_FEMENINAS,
  EJEMPLO_SIN_VOCES_FEMENINAS,
  ...LISTA_EJEMPLOS.map((e) => e.resultado),
];

describe("Contrato de datos de Athenis Voces (v0.2)", () => {
  it("todos los ejemplos tienen versión de contrato '0.2'", () => {
    for (const r of RESULTADOS) {
      expect(r.version_contrato).toBe(VERSION_CONTRATO);
    }
  });

  it("los hablantes están numerados desde 1 (RN-10)", () => {
    for (const ej of RESULTADOS) {
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

  it("hay exactamente 2 ejemplos precalculados en la lista (RF-02)", () => {
    expect(LISTA_EJEMPLOS.length).toBe(2);
  });
});

// T044 (FR-015, RD-02): los tipos del contrato salen del OpenAPI del servidor, no se escriben a mano.
// Las comprobaciones de tipos las verifica tsc (pnpm build); vitest no las ejecuta.
describe("Tipos generados desde el OpenAPI del servidor", () => {
  it("existe el módulo generado types/api", async () => {
    await expect(import("../types/api")).resolves.toBeDefined();
  });

  it("los tipos del contrato son los del esquema, con todos los campos obligatorios", () => {
    expectTypeOf<Resultado>().toEqualTypeOf<Completo<Esquemas["Resultado"]>>();
    expectTypeOf<EstadoAnalisis>().toEqualTypeOf<Completo<Esquemas["EstadoAnalisis"]>>();
    expectTypeOf<HablantesParaConfirmar>().toEqualTypeOf<
      Completo<Esquemas["HablantesParaConfirmar"]>
    >();
    expectTypeOf<Confirmacion>().toEqualTypeOf<Completo<Esquemas["Confirmacion"]>>();
    expectTypeOf<MetricasHablante>().toEqualTypeOf<Completo<Esquemas["MetricasHablante"]>>();
  });

  it("Completo también vale para los objetos anidados de Resultado", () => {
    expectTypeOf<Resultado["hablantes"][number]["indice_protagonismo"]>().toEqualTypeOf<
      number | null
    >();
    expectTypeOf<Resultado["grupos"][number]["cuota_tiempo"]>().toEqualTypeOf<number | null>();
    expectTypeOf<Resultado["primera_intervencion_femenina"]>().toEqualTypeOf<number | null>();
    expectTypeOf<EstadoAnalisis["progreso"]>().toEqualTypeOf<number | null>();
    expectTypeOf<Hablante["propuesta"]>().toEqualTypeOf<PropuestaVoz | null>();
  });
});
