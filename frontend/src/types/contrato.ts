/**
 * Contrato de datos de Athenis Voces - Versión 0.2
 *
 * Mapeo exacto de docs/contrato_de_datos.md y backend/src/contrato.py.
 * Ningún nombre difiere del backend. Tiempos en segundos con decimales.
 */

export const VERSION_CONTRATO = "0.2";

export type EtiquetaVoz = "femenino" | "masculino" | "indeterminado";

export type OrigenEtiqueta = "modelo" | "persona";

export type Estado = "en_cola" | "procesando" | "esperando_confirmacion" | "terminado" | "error";

export type TipoSolapamiento = "con_exito" | "intento" | "senal_de_escucha";

export type NombreIndice = "ratio_representacion" | "brecha_interrupcion";

export interface Tramo {
  inicio: number;
  fin: number;
}

export interface Turno extends Tramo {
  hablante: number;
}

export interface Solapamiento extends Tramo {
  hablantes: number[];
}

export interface Fragmento extends Tramo {}

export interface PropuestaVoz {
  etiqueta: EtiquetaVoz;
  confianza: number; // entre 0 y 1; entre 0.35 y 0.65 es propuesta dudosa
}

export interface Hablante {
  hablante: number;
  segundos_habla: number;
  propuesta: PropuestaVoz | null; // null en modo manual
  fragmentos: Fragmento[];
}

export interface HablantesParaConfirmar {
  version_contrato: string;
  id_analisis: string;
  hablantes: Hablante[];
}

export interface EtiquetaConfirmada {
  hablante: number;
  etiqueta: EtiquetaVoz;
  origen: OrigenEtiqueta;
}

export interface Confirmacion {
  version_contrato: string;
  etiquetas: EtiquetaConfirmada[];
}

export interface EstadoAnalisis {
  version_contrato: string;
  id_analisis: string;
  estado: Estado;
  progreso: number | null; // solo en 'procesando'
  motivo_error: string | null; // solo en 'error'
}

export interface Interrupcion extends Tramo {
  interrumpe: number;
  interrumpido: number;
  tipo: TipoSolapamiento;
}

export interface MetricasHablante {
  hablante: number;
  etiqueta: EtiquetaVoz;
  origen: OrigenEtiqueta;
  segundos_habla: number;
  turnos: number;
  turnos_largos: number; // MD-06 (> 30s)
  abre: boolean; // MD-07 (primer turno > 5s)
  cierra: boolean; // MD-08 (último turno > 5s)
  interrupciones_recibidas: number;
  interrupciones_hechas: number;
  tasa_interrupcion_recibida: number | null; // cada 10 min de habla
  recupera_palabra: number | null; // % de interrupciones con éxito tras las que retoma en <= 10s
  apoyos_recibidos: number | null; // señales de escucha recibidas cada 10 min
  indice_protagonismo: number | null; // 0 a 100
}

export interface MetricasGrupo {
  etiqueta: EtiquetaVoz;
  numero_voces: number;
  segundos_habla: number;
  cuota_tiempo: number | null; // % del tiempo total de voces etiquetadas
  turnos: number;
  cuota_turnos: number | null;
  interrupciones_recibidas: number;
  tasa_interrupcion_recibida: number | null;
}

export interface Indice {
  nombre: NombreIndice;
  valor: number | null; // null = no aplicable
  formula: string;
}

export interface Resultado {
  version_contrato: string;
  id_analisis: string;
  duracion: number;
  voz_femenina_presente: boolean;
  primera_intervencion_femenina: number | null;
  segundos_voces_cortas: number; // voces < 10s o < 3 fragmentos (D-15, D-18)
  grupos: MetricasGrupo[];
  hablantes: MetricasHablante[];
  turnos: Turno[];
  solapamientos: Solapamiento[];
  interrupciones: Interrupcion[];
  indices: Indice[];
}

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
