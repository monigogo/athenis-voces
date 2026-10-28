import {
  AlertCircle,
  FileAudio,
  Loader2,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import type React from "react";
import { useRef, useState } from "react";
import { api } from "../services/api";
import {
  type EjemploPrecalculado,
  type EstadoAnalisis,
  type Resultado,
  formatearSegundos,
} from "../types/contrato";

interface Props {
  onAnalisisIniciado: (id: string) => void;
  onEjemploSeleccionado: (resultado: Resultado) => void;
}

export const AnalizarView: React.FC<Props> = ({ onAnalisisIniciado, onEjemploSeleccionado }) => {
  const [dragActive, setDragActive] = useState(false);
  const [archivoSeleccionado, setArchivoSeleccionado] = useState<File | null>(null);
  const [estadoAnalisis, setEstadoAnalisis] = useState<EstadoAnalisis | null>(null);
  const [errorSubida, setErrorSubida] = useState<string | null>(null);
  const [procesandoEjemplo, setProcesandoEjemplo] = useState<string | null>(null);
  const [modoManual, setModoManual] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const ejemplos = api.getEjemplos();

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const procesarArchivo = async (file: File) => {
    setErrorSubida(null);
    setArchivoSeleccionado(file);

    try {
      await api.subirAudio(
        file,
        (nuevoEstado) => {
          setEstadoAnalisis(nuevoEstado);
          if (nuevoEstado.estado === "esperando_confirmacion") {
            onAnalisisIniciado(nuevoEstado.id_analisis);
          }
        },
        modoManual,
      );
    } catch (err: unknown) {
      const mensaje = err instanceof Error ? err.message : "Error al procesar el audio";
      setErrorSubida(mensaje);
      setEstadoAnalisis(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) {
      procesarArchivo(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      procesarArchivo(e.target.files[0]);
    }
  };

  const handleCargarEjemplo = async (ej: EjemploPrecalculado) => {
    setProcesandoEjemplo(ej.id);
    try {
      const res = await api.iniciarEjemplo(ej.id);
      onEjemploSeleccionado(res);
    } finally {
      setProcesandoEjemplo(null);
    }
  };

  const reintentarAnalisis = () => {
    if (archivoSeleccionado) {
      procesarArchivo(archivoSeleccionado);
    }
  };

  return (
    <div>
      {/* Aviso ético obligatorio antes de subir (8.4) */}
      <div className="notice-box">
        <ShieldCheck
          size={20}
          color="var(--accent-primary)"
          style={{ flexShrink: 0, marginTop: "2px" }}
        />
        <div>
          <strong>Aviso de privacidad y ética acústica:</strong>
          <p style={{ marginTop: "0.25rem" }}>
            «Analizaremos solo las voces de este audio, no lo que se dice. No identificamos a nadie
            y borramos el audio pasadas 24 horas. Sube solo audios que tengas derecho a usar.»
            (Sección 8.4)
          </p>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
          gap: "2rem",
          marginBottom: "3rem",
        }}
      >
        {/* Zona de subida */}
        <div className="card" style={{ display: "flex", flexDirection: "column" }}>
          <h2
            style={{
              fontSize: "1.25rem",
              marginBottom: "0.5rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <UploadCloud size={22} color="var(--accent-primary)" />
            Subir audio para análisis
          </h2>
          <p
            style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1.5rem" }}
          >
            Admite archivos .mp3, .wav, .m4a, .ogg o .flac. El pipeline detecta voces, diariza y
            extrae fragmentos para confirmación humana obligatoria.
          </p>

          {/* Modo manual: se elige antes de subir; las voces llegan sin propuesta (RF-08) */}
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              fontSize: "0.85rem",
              marginBottom: "1rem",
              cursor: "pointer",
            }}
          >
            <input
              type="checkbox"
              checked={modoManual}
              onChange={(e) => setModoManual(e.target.checked)}
            />
            Modo manual: confirmar las voces sin ver la propuesta del modelo
          </label>

          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*,.mp3,.wav,.m4a,.ogg,.flac"
            style={{ display: "none" }}
            onChange={handleFileChange}
          />

          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{
              flex: 1,
              minHeight: "220px",
              border: `2px dashed ${dragActive ? "var(--accent-primary)" : "var(--border-subtle)"}`,
              borderRadius: "var(--radius-lg)",
              background: dragActive ? "rgba(45, 212, 191, 0.05)" : "var(--bg-surface-elevated)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              padding: "2rem",
              textAlign: "center",
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
          >
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: "50%",
                background: "rgba(45, 212, 191, 0.12)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--accent-primary)",
                marginBottom: "1rem",
              }}
            >
              <FileAudio size={28} />
            </div>

            <div style={{ fontWeight: 700, fontSize: "1rem", marginBottom: "0.35rem" }}>
              Arrastra un archivo de audio aquí o haz clic para seleccionarlo
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Límite de audio conversacional. Se analizará en local sin salir a servidores externos.
            </div>
          </div>

          {/* Estado del análisis en curso */}
          {estadoAnalisis && (
            <div
              style={{
                marginTop: "1.25rem",
                padding: "1rem",
                borderRadius: "var(--radius-md)",
                background: "var(--bg-surface-elevated)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "0.5rem",
                }}
              >
                <span
                  style={{
                    fontSize: "0.85rem",
                    fontWeight: 600,
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  {estadoAnalisis.estado === "procesando" && (
                    <Loader2 size={16} className="status-dot pulsing" />
                  )}
                  {estadoAnalisis.estado === "en_cola" && "En cola de procesamiento..."}
                  {estadoAnalisis.estado === "procesando" &&
                    `Procesando pipeline (${estadoAnalisis.progreso?.toFixed(0)}%)`}
                  {estadoAnalisis.estado === "esperando_confirmacion" && (
                    <span style={{ color: "var(--accent-primary)" }}>
                      ¡Fase 1 terminada! Redirigiendo a Confirmar voces...
                    </span>
                  )}
                  {estadoAnalisis.estado === "error" && (
                    <span style={{ color: "#ef4444" }}>Error en el análisis</span>
                  )}
                </span>
                {estadoAnalisis.progreso !== null && (
                  <span
                    className="mono-num"
                    style={{ fontSize: "0.8rem", color: "var(--accent-primary)" }}
                  >
                    {estadoAnalisis.progreso}%
                  </span>
                )}
              </div>

              {/* Barra de progreso */}
              {estadoAnalisis.progreso !== null && (
                <div
                  style={{
                    height: "8px",
                    background: "rgba(0,0,0,0.4)",
                    borderRadius: "4px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${estadoAnalisis.progreso}%`,
                      background: "linear-gradient(90deg, #14b8a6, #2dd4bf)",
                      transition: "width 0.4s ease",
                    }}
                  />
                </div>
              )}

              {/* Detalle de fases del pipeline (RF-04) */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(4, 1fr)",
                  gap: "0.5rem",
                  marginTop: "0.75rem",
                  fontSize: "0.7rem",
                  color: "var(--text-muted)",
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    color: (estadoAnalisis.progreso ?? 0) >= 0 ? "var(--text-primary)" : "inherit",
                  }}
                >
                  1. Preparar
                </div>
                <div
                  style={{
                    color: (estadoAnalisis.progreso ?? 0) >= 25 ? "var(--text-primary)" : "inherit",
                  }}
                >
                  2. Diarizar
                </div>
                <div
                  style={{
                    color: (estadoAnalisis.progreso ?? 0) >= 50 ? "var(--text-primary)" : "inherit",
                  }}
                >
                  3. Proponer voz
                </div>
                <div
                  style={{
                    color: (estadoAnalisis.progreso ?? 0) >= 75 ? "var(--text-primary)" : "inherit",
                  }}
                >
                  4. Fragmentos
                </div>
              </div>
            </div>
          )}

          {/* Error y reintento sin resubir (FR-004, 8.1) */}
          {errorSubida && (
            <div
              style={{
                marginTop: "1.25rem",
                padding: "1rem",
                borderRadius: "var(--radius-md)",
                background: "rgba(239, 68, 68, 0.1)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                color: "#ef4444",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "1rem",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  fontSize: "0.85rem",
                }}
              >
                <AlertCircle size={18} />
                <span>{errorSubida}</span>
              </div>
              <button onClick={reintentarAnalisis} className="btn btn-secondary btn-sm">
                <RotateCcw size={14} /> Reintentar
              </button>
            </div>
          )}
        </div>

        {/* Sección de ejemplos precalculados (RF-02, Must) */}
        <div className="card">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "0.5rem",
            }}
          >
            <h2
              style={{ fontSize: "1.25rem", display: "flex", alignItems: "center", gap: "0.5rem" }}
            >
              <Sparkles size={20} color="var(--accent-primary)" />
              Episodios de ejemplo precalculados
            </h2>
            <span className="badge-tag">Acceso instantáneo &lt; 2s</span>
          </div>

          <p
            style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1.25rem" }}
          >
            Resultados del sistema sobre reuniones reales del corpus AMI, para explorar las métricas
            de inmediato sin esperar el procesamiento acústico. Las voces no las ha confirmado
            ninguna persona (RF-02, RNF-02).
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {ejemplos.map((ej) => {
              const estaCargando = procesandoEjemplo === ej.id;

              return (
                <div
                  key={ej.id}
                  style={{
                    padding: "1.15rem",
                    borderRadius: "var(--radius-md)",
                    background: "var(--bg-surface-elevated)",
                    border: "1px solid var(--border-subtle)",
                    transition: "all 0.2s ease",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      marginBottom: "0.4rem",
                    }}
                  >
                    <h3 style={{ fontSize: "1rem", fontWeight: 700 }}>{ej.nombre}</h3>
                    <span
                      className="mono-num"
                      style={{
                        fontSize: "0.75rem",
                        padding: "0.15rem 0.5rem",
                        borderRadius: "var(--radius-full)",
                        background: "rgba(255,255,255,0.06)",
                        color: "var(--text-secondary)",
                      }}
                    >
                      {formatearSegundos(ej.duracion)} · {ej.total_hablantes} voces
                    </span>
                  </div>

                  <p
                    style={{
                      fontSize: "0.825rem",
                      color: "var(--text-secondary)",
                      lineHeight: 1.5,
                      marginBottom: "0.85rem",
                    }}
                  >
                    {ej.descripcion}
                  </p>

                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      {ej.origen}
                    </span>

                    <button
                      onClick={() => handleCargarEjemplo(ej)}
                      disabled={estaCargando}
                      className="btn btn-primary btn-sm"
                      style={{ display: "inline-flex", gap: "0.4rem" }}
                    >
                      {estaCargando ? (
                        <Loader2 size={14} className="status-dot pulsing" />
                      ) : (
                        <Play size={14} />
                      )}
                      Ver resultados
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
