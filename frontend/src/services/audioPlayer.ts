/**
 * Reproductor de fragmentos de audio: muestras de voz, turnos e interrupciones (RF-07, RF-17, RF-18).
 *
 * - Con backend, cada fragmento es el WAV de GET /analisis/{id}/fragmento
 *   (specs/003-producto/contracts/api-http.md); si el backend lo rechaza, se muestra su motivo.
 * - Sin backend (modo demo), suena el tramo del audio subido, decodificado en el navegador.
 * - Los ejemplos precalculados no tienen audio: no suena nada.
 * - Los tramos llegan ya recortados por tramoDeEvento y tramoDeVoz (services/api.ts):
 *   15 s como máximo y, en las interrupciones, como mucho 1 s antes del evento.
 */

/** Lo más largo que suena un fragmento (9.3, RF-18). */
const MAX_DURACION_S = 15;

class AudioService {
  private ctx: AudioContext | null = null;
  private currentSource: AudioBufferSourceNode | null = null;
  private userAudioBuffer: AudioBuffer | null = null;
  private isPlaying = false;
  private activeTimer: number | null = null;
  /** Cambia con cada parada: un fragmento que llega después ya no suena. */
  private peticiones = 0;
  private onStateChange: ((playing: boolean, progress: number) => void) | null = null;

  private getContext(): AudioContext {
    if (!this.ctx || this.ctx.state === "suspended") {
      const AudioCtx =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new AudioCtx();
    }
    if (this.ctx.state === "suspended") {
      this.ctx.resume();
    }
    return this.ctx;
  }

  /** Carga un archivo de audio real subido por la usuaria */
  async loadUserAudio(file: File): Promise<void> {
    const ctx = this.getContext();
    const arrayBuffer = await file.arrayBuffer();
    this.userAudioBuffer = await ctx.decodeAudioData(arrayBuffer);
  }

  /** Detiene cualquier reproducción en curso, también un fragmento que aún se está descargando */
  stop(): void {
    this.peticiones++;
    if (this.currentSource) {
      try {
        this.currentSource.stop();
      } catch {
        // Ignorar si ya terminó
      }
      this.currentSource.disconnect();
      this.currentSource = null;
    }
    if (this.activeTimer) {
      clearInterval(this.activeTimer);
      this.activeTimer = null;
    }
    this.isPlaying = false;
    if (this.onStateChange) {
      this.onStateChange(false, 0);
    }
  }

  /**
   * Reproduce un tramo [inicio, fin] ya recortado (los tramos salen de tramoDeEvento y tramoDeVoz).
   * Con `url`, suena el WAV que devuelve el backend; si responde con error, se lanza su motivo.
   * Sin `url`, suena el tramo del audio cargado en local (modo demo); si no hay, no suena nada.
   */
  async playSegment(
    inicio: number,
    fin: number,
    onProgress?: (playing: boolean, progress: number) => void,
    url?: string,
  ): Promise<void> {
    this.stop();
    this.onStateChange = onProgress || null;
    const peticion = this.peticiones;

    if (url) {
      const res = await fetch(url);
      if (!res.ok) {
        const cuerpo = await res.json().catch(() => null);
        const detalle = cuerpo?.detail;
        throw new Error(
          typeof detalle === "string"
            ? detalle
            : `El servidor respondió con el error ${res.status}`,
        );
      }
      const buffer = await this.getContext().decodeAudioData(await res.arrayBuffer());
      // Si mientras tanto se paró o se pidió otro fragmento, este ya no suena
      if (peticion !== this.peticiones) return;
      this.reproducir(buffer, 0, Math.min(buffer.duration, MAX_DURACION_S));
      return;
    }

    if (this.userAudioBuffer) {
      const duracion = Math.min(Math.max(fin - inicio, 0.5), MAX_DURACION_S);
      this.reproducir(this.userAudioBuffer, Math.max(0, inicio), duracion);
    }
  }

  private reproducir(buffer: AudioBuffer, desde: number, duracion: number): void {
    const ctx = this.getContext();
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);

    source.onended = () => {
      this.stop();
    };

    this.currentSource = source;
    this.isPlaying = true;
    source.start(0, desde, duracion);

    const startTime = ctx.currentTime;
    this.activeTimer = window.setInterval(() => {
      const elapsed = ctx.currentTime - startTime;
      const progress = Math.min(elapsed / duracion, 1.0);
      if (this.onStateChange) {
        this.onStateChange(true, progress);
      }
      if (progress >= 1.0) {
        this.stop();
      }
    }, 50);
  }

  get playing(): boolean {
    return this.isPlaying;
  }
}

export const audioService = new AudioService();
