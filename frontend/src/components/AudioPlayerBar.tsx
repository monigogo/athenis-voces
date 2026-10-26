import { Pause, Play, Square, Volume2 } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { audioService } from "../services/audioPlayer";

interface Props {
  currentTrack: {
    titulo: string;
    inicio: number;
    fin: number;
    hablante?: number;
  } | null;
  onClose?: () => void;
}

export const AudioPlayerBar: React.FC<Props> = ({ currentTrack }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!currentTrack) {
      setIsPlaying(false);
      setProgress(0);
      return;
    }

    // Al seleccionar una pista, iniciar automáticamente
    audioService.playSegment(
      currentTrack.inicio,
      currentTrack.fin,
      currentTrack.hablante || 1,
      (playing, prog) => {
        setIsPlaying(playing);
        setProgress(prog);
      },
    );

    return () => {
      audioService.stop();
    };
  }, [currentTrack]);

  if (!currentTrack) return null;

  const duracionTotal = Math.min(Math.max(currentTrack.fin - currentTrack.inicio, 0.5), 15.0);
  const tiempoTranscurrido = (duracionTotal * progress).toFixed(1);

  const togglePlay = () => {
    if (isPlaying) {
      audioService.stop();
      setIsPlaying(false);
    } else {
      audioService.playSegment(
        currentTrack.inicio,
        currentTrack.fin,
        currentTrack.hablante || 1,
        (playing, prog) => {
          setIsPlaying(playing);
          setProgress(prog);
        },
      );
    }
  };

  return (
    <section
      style={{
        position: "fixed",
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 60,
        background: "rgba(18, 24, 36, 0.95)",
        backdropFilter: "blur(16px)",
        borderTop: "1px solid var(--border-subtle)",
        boxShadow: "0 -4px 20px rgba(0,0,0,0.5)",
        padding: "0.85rem 1.5rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "1.5rem",
      }}
      aria-label="Reproductor de audio"
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.85rem", minWidth: "220px" }}>
        <button
          onClick={togglePlay}
          className="btn btn-primary"
          style={{ width: "40px", height: "40px", padding: 0, borderRadius: "50%" }}
          aria-label={isPlaying ? "Pausar reproducción" : "Reanudar reproducción"}
        >
          {isPlaying ? <Pause size={18} /> : <Play size={18} />}
        </button>

        <button
          onClick={() => audioService.stop()}
          className="btn btn-secondary btn-sm"
          style={{ width: "32px", height: "32px", padding: 0 }}
          aria-label="Detener audio"
        >
          <Square size={14} />
        </button>

        <div>
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)" }}>
            {currentTrack.titulo}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Tramo: {currentTrack.inicio.toFixed(1)}s - {currentTrack.fin.toFixed(1)}s (máx 15s)
          </div>
        </div>
      </div>

      {/* Barra de progreso interactiva con onda */}
      <div style={{ flex: 1, maxWidth: "600px" }}>
        <div
          style={{
            height: "8px",
            background: "var(--bg-surface-elevated)",
            borderRadius: "4px",
            overflow: "hidden",
            position: "relative",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              bottom: 0,
              width: `${progress * 100}%`,
              background: "linear-gradient(90deg, #14b8a6, #2dd4bf)",
              transition: "width 0.05s linear",
            }}
          />
        </div>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: "0.75rem",
            color: "var(--text-muted)",
            marginTop: "0.25rem",
            fontFamily: "var(--font-mono)",
          }}
        >
          <span>{tiempoTranscurrido}s</span>
          <span>{duracionTotal.toFixed(1)}s</span>
        </div>
      </div>

      {/* Control de audio y aviso de privacidad */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.65rem",
          fontSize: "0.75rem",
          color: "var(--text-muted)",
        }}
      >
        <Volume2 size={16} color="var(--accent-primary)" />
        <span className="badge-tag">Fragmento auditivo acústico</span>
      </div>
    </section>
  );
};
