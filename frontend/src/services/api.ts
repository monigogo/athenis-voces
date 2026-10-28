/**
 * Cliente de API para Athenis Voces.
 *
 * Implementa las rutas de la sección 9.3 del documento funcional:
 * - POST /analisis
 * - GET /analisis/{id}
 * - GET /analisis/{id}/hablantes
 * - POST /analisis/{id}/confirmacion
 * - GET /analisis/{id}/resultado
 * - GET /analisis/{id}/fragmento?inicio=&fin=
 * - GET /ejemplos
 * - GET /salud
 *
 * Con el backend conectado (GET /salud responde) usa sus rutas de verdad: specs/003-producto/
 * contracts/api-http.md. Sin backend, sigue el modo demo integrado (plan, Parte 8).
 */

import { LISTA_EJEMPLOS } from "../data/ejemplos";
import { EJEMPLO_CON_VOCES_FEMENINAS, EJEMPLO_SIN_VOCES_FEMENINAS } from "../data/simulacion";
import type {
  Confirmacion,
  EjemploPrecalculado,
  Estado,
  EstadoAnalisis,
  HablantesParaConfirmar,
  Resultado,
} from "../types/contrato";
import { audioService } from "./audioPlayer";

const API_BASE = "/api";

/** Lo más largo que puede durar un fragmento (9.3, RF-18): el backend rechaza tramos mayores. */
const MAX_FRAGMENTO_S = 15;
/** Lo que se oye antes de una interrupción: «empieza como mucho 1 s antes del evento» (RF-18). */
const ANTES_DEL_EVENTO_S = 1;
/**
 * Lo que se oye después de una interrupción: RF-18 pide que el fragmento «acaba después».
 * El valor no está fijado en ningún documento.
 */
const DESPUES_DEL_EVENTO_S = 0.5;

export interface Tramo {
  inicio: number;
  fin: number;
}

/** Tramo de una interrupción (RF-18): 1 s antes, un poco después y 15 s como máximo. */
export function tramoDeEvento(inicio: number, fin: number, duracion: number): Tramo {
  const desde = Math.max(0, inicio - ANTES_DEL_EVENTO_S);
  const hasta = Math.min(fin + DESPUES_DEL_EVENTO_S, duracion, desde + MAX_FRAGMENTO_S);
  return { inicio: desde, fin: hasta };
}

/** Tramo de una muestra de voz o de un turno: tal cual, con el tope de 15 s y la duración si se conoce. */
export function tramoDeVoz(
  inicio: number,
  fin: number,
  duracion = Number.POSITIVE_INFINITY,
): Tramo {
  const desde = Math.max(0, inicio);
  return { inicio: desde, fin: Math.min(fin, duracion, desde + MAX_FRAGMENTO_S) };
}

/** Ruta del WAV de un tramo (GET /analisis/{id}/fragmento). */
export function urlFragmento(idAnalisis: string, { inicio, fin }: Tramo): string {
  const consulta = new URLSearchParams({ inicio: String(inicio), fin: String(fin) });
  return `${API_BASE}/analisis/${encodeURIComponent(idAnalisis)}/fragmento?${consulta}`;
}

interface Opciones {
  /** Cada cuánto se pregunta el estado de un análisis en marcha. */
  intervaloMs?: number;
}

export class ApiClient {
  private readonly intervaloMs: number;

  constructor(opciones: Opciones = {}) {
    this.intervaloMs = opciones.intervaloMs ?? 1000;
  }

  private backendAvailable: boolean | null = null;
  private localState: {
    id_analisis: string;
    estado: EstadoAnalisis;
    hablantes: HablantesParaConfirmar | null;
    resultado: Resultado | null;
    archivoAudio?: File;
  } | null = null;

  async checkSalud(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/salud`, { signal: AbortSignal.timeout(1200) });
      this.backendAvailable = res.ok;
      return res.ok;
    } catch {
      this.backendAvailable = false;
      return false;
    }
  }

  isBackendConnected(): boolean {
    return !!this.backendAvailable;
  }

  /** Si el análisis actual tiene audio: los ejemplos precalculados no lo tienen. */
  hayAudio(): boolean {
    return !!this.localState?.archivoAudio;
  }

  /** URL del fragmento en el backend; null si no hay backend o el análisis no tiene audio. */
  urlFragmentoActual(tramo: Tramo): string | null {
    if (!this.backendAvailable || !this.localState?.archivoAudio) return null;
    return urlFragmento(this.localState.id_analisis, tramo);
  }

  /** Pide una ruta y devuelve su JSON; si falla, el motivo que da el backend (`detail`). */
  private async pedir<T>(ruta: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE}${ruta}`, init);
    const cuerpo = await res.json().catch(() => null);
    if (!res.ok) {
      const detalle = cuerpo?.detail;
      throw new Error(
        typeof detalle === "string" ? detalle : `El servidor respondió con el error ${res.status}`,
      );
    }
    return cuerpo as T;
  }

  /** Pregunta el estado hasta llegar a uno de `hasta`. Un «error» se lanza con su motivo (RNF-16). */
  private async esperar(
    id: string,
    hasta: Estado[],
    onProgreso?: (estado: EstadoAnalisis) => void,
  ): Promise<EstadoAnalisis> {
    for (;;) {
      const estado = await this.pedir<EstadoAnalisis>(`/analisis/${encodeURIComponent(id)}`);
      onProgreso?.(estado);
      if (estado.estado === "error") {
        throw new Error(estado.motivo_error ?? "El análisis no ha podido terminar.");
      }
      if (hasta.includes(estado.estado)) return estado;
      await new Promise((r) => setTimeout(r, this.intervaloMs));
    }
  }

  getEjemplos(): EjemploPrecalculado[] {
    return LISTA_EJEMPLOS;
  }

  /**
   * Inicia el análisis de un ejemplo precalculado.
   * Tarda menos de 2 s y va directo al resultado (RF-02, SC-001, 8.1).
   */
  async iniciarEjemplo(ejemploId: string): Promise<Resultado> {
    const ejemplo = LISTA_EJEMPLOS.find((e) => e.id === ejemploId) || LISTA_EJEMPLOS[0];
    audioService.stop();

    if (this.backendAvailable) {
      // El nombre y la descripción son de la web; los datos, del backend (los ids coinciden)
      const formulario = new FormData();
      formulario.append("ejemplo", ejemplo.id);
      const creado = await this.pedir<EstadoAnalisis>("/analisis", {
        method: "POST",
        body: formulario,
      });
      const resultado = await this.getResultadoDelBackend(creado.id_analisis);
      this.localState = {
        id_analisis: creado.id_analisis,
        estado: creado,
        hablantes: null,
        resultado,
      };
      return resultado;
    }

    this.localState = {
      id_analisis: ejemplo.id,
      estado: {
        version_contrato: "0.2",
        id_analisis: ejemplo.id,
        estado: "terminado",
        progreso: null,
        motivo_error: null,
      },
      hablantes: null,
      resultado: ejemplo.resultado,
    };

    return ejemplo.resultado;
  }

  /**
   * Sube un audio y arranca la Fase 1 del pipeline (RF-01, RF-04).
   */
  async subirAudio(
    archivo: File,
    onProgreso: (estado: EstadoAnalisis) => void,
    modoManual = false,
  ): Promise<{ id_analisis: string }> {
    // Validar tipo de audio por extensión y mime
    const extensionesPermitidas = [".mp3", ".wav", ".m4a", ".ogg", ".flac"];
    const extValida = extensionesPermitidas.some((ext) => archivo.name.toLowerCase().endsWith(ext));
    const mimeValido = archivo.type.startsWith("audio/") || extValida;

    if (!mimeValido) {
      throw new Error(
        "Formato no admitido: se requieren archivos de audio válidos (mp3, wav, m4a, ogg, flac).",
      );
    }

    // Sin backend, el reproductor usa el audio local. Con backend, los fragmentos los da el
    // servidor: decodificar aquí una reunión larga bloquearía la subida
    if (!this.backendAvailable) await audioService.loadUserAudio(archivo);

    if (this.backendAvailable) {
      const formulario = new FormData();
      formulario.append("audio", archivo);
      formulario.append("modo_manual", String(modoManual));
      const creado = await this.pedir<EstadoAnalisis>("/analisis", {
        method: "POST",
        body: formulario,
      });
      onProgreso(creado);
      const listo = await this.esperar(
        creado.id_analisis,
        ["esperando_confirmacion", "terminado"],
        onProgreso,
      );
      this.localState = {
        id_analisis: creado.id_analisis,
        archivoAudio: archivo,
        estado: listo,
        hablantes: null,
        resultado: null,
      };
      return { id_analisis: creado.id_analisis };
    }

    const id = `analisis-${Date.now().toString(36)}`;
    this.localState = {
      id_analisis: id,
      archivoAudio: archivo,
      estado: {
        version_contrato: "0.2",
        id_analisis: id,
        estado: "en_cola",
        progreso: null,
        motivo_error: null,
      },
      hablantes: null,
      resultado: null,
    };

    onProgreso(this.localState.estado);

    // Simular el avance de las fases del pipeline (RF-04):
    // 0%: preparar el audio -> 25%: separar las voces -> 50%: proponer la voz -> 75%: fragmentos
    const pasos = [
      { progreso: 0.0, delay: 500 },
      { progreso: 25.0, delay: 800 },
      { progreso: 50.0, delay: 900 },
      { progreso: 75.0, delay: 700 },
    ];

    for (const paso of pasos) {
      await new Promise((r) => setTimeout(r, paso.delay));
      this.localState.estado = {
        version_contrato: "0.2",
        id_analisis: id,
        estado: "procesando",
        progreso: paso.progreso,
        motivo_error: null,
      };
      onProgreso(this.localState.estado);
    }

    await new Promise((r) => setTimeout(r, 600));

    // Generar hablantes para confirmar según el tamaño del audio
    const hablantesParaConfirmar: HablantesParaConfirmar = {
      version_contrato: "0.2",
      id_analisis: id,
      hablantes: [
        {
          hablante: 1,
          segundos_habla: 78.4,
          propuesta: { etiqueta: "femenino", confianza: 0.88 },
          fragmentos: [
            { inicio: 2.0, fin: 5.5 },
            { inicio: 24.0, fin: 28.0 },
            { inicio: 55.0, fin: 59.2 },
          ],
        },
        {
          hablante: 2,
          segundos_habla: 65.2,
          propuesta: { etiqueta: "masculino", confianza: 0.92 },
          fragmentos: [
            { inicio: 10.0, fin: 14.2 },
            { inicio: 42.0, fin: 46.5 },
            { inicio: 70.0, fin: 73.8 },
          ],
        },
        {
          hablante: 3,
          segundos_habla: 46.1,
          // Caso de propuesta dudosa (RF-06: confianza entre 0.35 y 0.65)
          propuesta: { etiqueta: "femenino", confianza: 0.52 },
          fragmentos: [
            { inicio: 18.0, fin: 22.1 },
            { inicio: 48.0, fin: 52.0 },
            { inicio: 80.0, fin: 84.5 },
          ],
        },
      ],
    };

    // En modo manual no hay propuesta: la persona decide a ciegas (RF-08)
    if (modoManual) {
      for (const h of hablantesParaConfirmar.hablantes) h.propuesta = null;
    }

    this.localState.hablantes = hablantesParaConfirmar;
    this.localState.estado = {
      version_contrato: "0.2",
      id_analisis: id,
      estado: "esperando_confirmacion",
      progreso: null,
      motivo_error: null,
    };
    onProgreso(this.localState.estado);

    return { id_analisis: id };
  }

  async getHablantes(idAnalisis: string): Promise<HablantesParaConfirmar> {
    if (this.backendAvailable) {
      return this.pedir<HablantesParaConfirmar>(
        `/analisis/${encodeURIComponent(idAnalisis)}/hablantes`,
      );
    }
    if (
      this.localState &&
      this.localState.id_analisis === idAnalisis &&
      this.localState.hablantes
    ) {
      return this.localState.hablantes;
    }
    // Fallback de demostración
    return {
      version_contrato: "0.2",
      id_analisis: idAnalisis,
      hablantes: [
        {
          hablante: 1,
          segundos_habla: 75.8,
          propuesta: { etiqueta: "femenino", confianza: 0.86 },
          fragmentos: [
            { inicio: 2.0, fin: 6.0 },
            { inicio: 18.0, fin: 22.5 },
            { inicio: 40.0, fin: 44.0 },
          ],
        },
        {
          hablante: 2,
          segundos_habla: 64.5,
          propuesta: { etiqueta: "masculino", confianza: 0.91 },
          fragmentos: [
            { inicio: 10.0, fin: 14.5 },
            { inicio: 28.0, fin: 32.0 },
            { inicio: 52.0, fin: 56.5 },
          ],
        },
        {
          hablante: 3,
          segundos_habla: 56.2,
          propuesta: { etiqueta: "femenino", confianza: 0.48 }, // Propuesta dudosa (RF-06)
          fragmentos: [
            { inicio: 14.0, fin: 18.0 },
            { inicio: 35.0, fin: 39.0 },
            { inicio: 62.0, fin: 66.0 },
          ],
        },
      ],
    };
  }

  /**
   * Envía las etiquetas confirmadas por la analista (Fase 2, RF-07).
   */
  async enviarConfirmacion(idAnalisis: string, confirmacion: Confirmacion): Promise<Resultado> {
    if (this.backendAvailable) {
      // El backend comprueba que se confirman justo las voces presentes (RF-07)
      await this.pedir<EstadoAnalisis>(`/analisis/${encodeURIComponent(idAnalisis)}/confirmacion`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(confirmacion),
      });
      await this.esperar(idAnalisis, ["terminado"]);
      const resultado = await this.getResultadoDelBackend(idAnalisis);
      if (this.localState?.id_analisis === idAnalisis) this.localState.resultado = resultado;
      return resultado;
    }
    // Validar que se hayan confirmado todos los hablantes
    const habs = await this.getHablantes(idAnalisis);
    const idsConfirmados = new Set(confirmacion.etiquetas.map((e) => e.hablante));
    for (const h of habs.hablantes) {
      if (!idsConfirmados.has(h.hablante)) {
        throw new Error(
          `Falta confirmar el Hablante ${h.hablante}. Hasta que no se confirmen todas las voces presentes, no hay resultados (RN-01, RF-07).`,
        );
      }
    }

    // Comprobar si hay voces femeninas en la confirmación
    const hayFemenina = confirmacion.etiquetas.some((e) => e.etiqueta === "femenino");
    const base = hayFemenina ? EJEMPLO_CON_VOCES_FEMENINAS : EJEMPLO_SIN_VOCES_FEMENINAS;

    // Adaptar hablantes con las etiquetas reales confirmadas por el usuario
    const resultadoFinal: Resultado = {
      ...base,
      id_analisis: idAnalisis,
      voz_femenina_presente: hayFemenina,
      hablantes: base.hablantes.map((h) => {
        const conf = confirmacion.etiquetas.find((e) => e.hablante === h.hablante);
        if (conf) {
          return {
            ...h,
            etiqueta: conf.etiqueta,
            origen: conf.origen,
          };
        }
        return h;
      }),
    };

    if (this.localState) {
      this.localState.resultado = resultadoFinal;
      this.localState.estado = {
        version_contrato: "0.2",
        id_analisis: idAnalisis,
        estado: "terminado",
        progreso: null,
        motivo_error: null,
      };
    }

    return resultadoFinal;
  }

  private getResultadoDelBackend(idAnalisis: string): Promise<Resultado> {
    return this.pedir<Resultado>(`/analisis/${encodeURIComponent(idAnalisis)}/resultado`);
  }

  async getResultado(idAnalisis: string): Promise<Resultado> {
    if (this.backendAvailable) return this.getResultadoDelBackend(idAnalisis);
    if (this.localState?.resultado) {
      return this.localState.resultado;
    }
    const ej = LISTA_EJEMPLOS.find((e) => e.id === idAnalisis);
    return ej ? ej.resultado : EJEMPLO_CON_VOCES_FEMENINAS;
  }
}

export const api = new ApiClient();
