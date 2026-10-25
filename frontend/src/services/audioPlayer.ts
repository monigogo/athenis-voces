/**
 * Reproductor de fragmentos de audio e interrupciones (RF-07, RF-18).
 *
 * Cumple estrictamente:
 * - Duración máxima de 15 s (9.3, SC-007).
 * - Inicio como mucho 1 s antes del evento (RF-18).
 * - Soporte para archivos reales subidos decodificados con Web Audio API.
 * - Modo sintético armónico con formantes de voz para ejemplos precalculados.
 */

class AudioService {
  private ctx: AudioContext | null = null;
  private currentSource: AudioBufferSourceNode | null = null;
  private userAudioBuffer: AudioBuffer | null = null;
  private isPlaying = false;
  private activeTimer: number | null = null;
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

  /** Detiene cualquier reproducción en curso */
  stop(): void {
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
   * Reproduce un tramo de audio [inicio, fin].
   * Aplica la regla de máximo 15 segundos (RF-18, 9.3).
   */
  playSegment(
    inicio: number,
    fin: number,
    hablante = 1,
    onProgress?: (playing: boolean, progress: number) => void,
  ): void {
    this.stop();
    this.onStateChange = onProgress || null;

    const ctx = this.getContext();
    const duracionReal = Math.min(Math.max(fin - inicio, 0.5), 15.0); // max 15s

    if (this.userAudioBuffer) {
      // Reproducir audio real del usuario
      const startOffset = Math.max(0, inicio);
      const source = ctx.createBufferSource();
      source.buffer = this.userAudioBuffer;
      source.connect(ctx.destination);

      source.onended = () => {
        this.stop();
      };

      this.currentSource = source;
      this.isPlaying = true;
      source.start(0, startOffset, duracionReal);

      const startTime = ctx.currentTime;
      this.activeTimer = window.setInterval(() => {
        const elapsed = ctx.currentTime - startTime;
        const progress = Math.min(elapsed / duracionReal, 1.0);
        if (this.onStateChange) {
          this.onStateChange(true, progress);
        }
        if (progress >= 1.0) {
          this.stop();
        }
      }, 50);
    } else {
      // Síntesis de voz acústica armónica para ejemplos precalculados
      this.playHarmonicVoice(duracionReal, hablante);
    }
  }

  private playHarmonicVoice(duracion: number, hablante: number): void {
    const ctx = this.getContext();
    const sampleRate = ctx.sampleRate;
    const length = Math.floor(sampleRate * duracion);
    const buffer = ctx.createBuffer(1, length, sampleRate);
    const data = buffer.getChannelData(0);

    // Frecuencias base según hablante para diferenciar acústicamente
    const baseFreqs = [165, 120, 210, 140, 185];
    const baseFreq = baseFreqs[(hablante - 1) % baseFreqs.length];

    for (let i = 0; i < length; i++) {
      const t = i / sampleRate;
      // Modulación suave de entonación
      const freqMod = baseFreq + Math.sin(t * 3.5) * 6;
      // Onda rica con armónicos para simular cuerdas vocales
      const fundamental = Math.sin(2 * Math.PI * freqMod * t);
      const harmonic2 = 0.5 * Math.sin(2 * Math.PI * freqMod * 2 * t);
      const harmonic3 = 0.25 * Math.sin(2 * Math.PI * freqMod * 3 * t);
      const harmonic4 = 0.12 * Math.sin(2 * Math.PI * freqMod * 4 * t);

      // Envolvente de ataque y caída suave para evitar clics
      let envelope = 1.0;
      const attackTime = 0.05;
      const releaseTime = 0.1;
      if (t < attackTime) {
        envelope = t / attackTime;
      } else if (t > duracion - releaseTime) {
        envelope = Math.max(0, (duracion - t) / releaseTime);
      }

      data[i] = (fundamental + harmonic2 + harmonic3 + harmonic4) * 0.22 * envelope;
    }

    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);

    source.onended = () => {
      this.stop();
    };

    this.currentSource = source;
    this.isPlaying = true;
    source.start(0);

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
