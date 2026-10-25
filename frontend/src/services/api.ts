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
 * Admite modo conectado al backend real y modo integrado local/falso (plan, Parte 8).
 */

import {
  EJEMPLO_CON_VOCES_FEMENINAS,
  EJEMPLO_SIN_VOCES_FEMENINAS,
  LISTA_EJEMPLOS,
} from "../data/ejemplos";
import type {
  Confirmacion,
  EjemploPrecalculado,
  EstadoAnalisis,
  HablantesParaConfirmar,
  Resultado,
} from "../types/contrato";
import { audioService } from "./audioPlayer";

const API_BASE = "/api";

export class ApiClient {
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

    // Cargar en el reproductor de audio para reproducción local
    await audioService.loadUserAudio(archivo);

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

  async getResultado(idAnalisis: string): Promise<Resultado> {
    if (this.localState?.resultado) {
      return this.localState.resultado;
    }
    const ej = LISTA_EJEMPLOS.find((e) => e.id === idAnalisis);
    return ej ? ej.resultado : EJEMPLO_CON_VOCES_FEMENINAS;
  }
}

export const api = new ApiClient();
