/**
 * Contrato de datos de Athenis Voces - Versión 0.2
 *
 * Los tipos salen del OpenAPI que publica el servidor (FR-015, RD-02): se generan en api.ts con
 * `pnpm tipos` y aquí solo se les da nombre. No se escriben a mano. Tiempos en segundos con
 * decimales.
 */

import type { components } from "./api";

export const VERSION_CONTRATO = "0.2";

/**
 * El OpenAPI marca como opcionales los campos que tienen valor por defecto (por ejemplo, los que
 * valen null si no aplican), pero el servidor siempre los envía. Completo los marca como
 * obligatorios, también en los objetos anidados.
 */
export type Completo<T> = T extends readonly (infer U)[]
  ? Completo<U>[]
  : T extends object
    ? { [K in keyof T]-?: Completo<T[K]> }
    : T;

type Esquema<N extends keyof components["schemas"]> = Completo<components["schemas"][N]>;

export type EtiquetaVoz = Esquema<"EtiquetaVoz">;
export type OrigenEtiqueta = Esquema<"OrigenEtiqueta">;
export type Estado = Esquema<"Estado">;
export type TipoSolapamiento = Esquema<"TipoSolapamiento">;
export type NombreIndice = Esquema<"NombreIndice">;

export type Turno = Esquema<"Turno">;
export type Solapamiento = Esquema<"Solapamiento">;
export type Fragmento = Esquema<"Fragmento">;
export type PropuestaVoz = Esquema<"PropuestaVoz">;
export type Hablante = Esquema<"Hablante">;
export type HablantesParaConfirmar = Esquema<"HablantesParaConfirmar">;
export type EtiquetaConfirmada = Esquema<"EtiquetaConfirmada">;
export type Confirmacion = Esquema<"Confirmacion">;
export type EstadoAnalisis = Esquema<"EstadoAnalisis">;
export type Interrupcion = Esquema<"Interrupcion">;
export type MetricasHablante = Esquema<"MetricasHablante">;
export type MetricasGrupo = Esquema<"MetricasGrupo">;
export type Indice = Esquema<"Indice">;
export type Resultado = Esquema<"Resultado">;

/** Datos de un ejemplo que solo usa la web (nombre y descripción): no están en el contrato. */
export interface EjemploPrecalculado {
  id: string;
  nombre: string;
  descripcion: string;
  origen: string;
  duracion: number;
  voces_femeninas: boolean;
  total_hablantes: number;
  resultado: Resultado;
}

/** Comprueba si una propuesta es dudosa (RF-06: entre 0.35 y 0.65 de confianza) */
export function esPropuestaDudosa(propuesta: PropuestaVoz | null): boolean {
  if (!propuesta) return false;
  return propuesta.confianza >= 0.35 && propuesta.confianza <= 0.65;
}

/** Formatea segundos en formato mm:ss o ss.s */
export function formatearSegundos(seg: number | null | undefined): string {
  if (seg === null || seg === undefined) return "no aplicable";
  const minutos = Math.floor(seg / 60);
  const segundos = Math.floor(seg % 60);
  const decimas = Math.floor((seg % 1) * 10);
  if (minutos > 0) {
    return `${minutos}m ${segundos.toString().padStart(2, "0")}s`;
  }
  return `${segundos}.${decimas}s`;
}
