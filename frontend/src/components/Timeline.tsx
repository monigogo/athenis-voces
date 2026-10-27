import { Layers, Volume2, ZoomIn, ZoomOut } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { tramoDeEvento, tramoDeVoz } from "../services/api";
import type { Interrupcion, MetricasHablante, Solapamiento, Turno } from "../types/contrato";

interface Props {
  duracion: number;
  hablantes: MetricasHablante[];
  turnos: Turno[];
  solapamientos: Solapamiento[];
  interrupciones: Interrupcion[];
  onPlaySegment: (inicio: number, fin: number, hablante?: number, titulo?: string) => void;
}

export const Timeline: React.FC<Props> = ({
  duracion,
  hablantes,
  turnos,
  solapamientos: _solapamientos,
  interrupciones,
  onPlaySegment,
}) => {
  const [zoom, setZoom] = useState(1);
  const [hoveredEvent, setHoveredEvent] = useState<string | null>(null);

  // Colores éticos por etiqueta
  const getEtiquetaColor = (etiqueta: string) => {
    switch (etiqueta) {
      case "femenino":
        return { fill: "#10b981", bg: "rgba(16, 185, 129, 0.28)", border: "#10b981" };
      case "masculino":
        return { fill: "#818cf8", bg: "rgba(129, 140, 248, 0.28)", border: "#818cf8" };
      default:
        return { fill: "#f59e0b", bg: "rgba(245, 158, 11, 0.28)", border: "#f59e0b" };
    }
  };

  const duracionTotal = Math.max(duracion, 1);
  const anchoBase = 100 * zoom; // %

  // Generar marcas de tiempo cada 30 segundos
  const marcasTiempo = [];
  const paso = duracionTotal > 180 ? 30 : 15;
  for (let s = 0; s <= duracionTotal; s += paso) {
    marcasTiempo.push(s);
  }

  return (
    <div className="card" style={{ marginBottom: "2rem" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1.25rem",
          flexWrap: "wrap",
          gap: "0.75rem",
        }}
      >
        <div>
          <h3 style={{ fontSize: "1.1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Layers size={18} color="var(--accent-primary)" />
            Línea de tiempo conversacional por hablante
          </h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Visualización interactiva de turnos, solapamientos e interrupciones. Haz clic en un
            bloque para escucharlo.
          </p>
        </div>

        {/* Controles de zoom */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <button
            onClick={() => setZoom((z) => Math.max(1, z - 0.5))}
            disabled={zoom <= 1}
            className="btn btn-secondary btn-sm"
            aria-label="Reducir zoom"
          >
            <ZoomOut size={14} />
          </button>
          <span
            style={{
              fontSize: "0.8rem",
              color: "var(--text-secondary)",
              minWidth: "40px",
              textAlign: "center",
            }}
          >
            {zoom}x
          </span>
          <button
            onClick={() => setZoom((z) => Math.min(3, z + 0.5))}
            disabled={zoom >= 3}
            className="btn btn-secondary btn-sm"
            aria-label="Aumentar zoom"
          >
            <ZoomIn size={14} />
          </button>
        </div>
      </div>

      {/* Leyenda */}
      <div
        style={{
          display: "flex",
          gap: "1.25rem",
          marginBottom: "1rem",
          fontSize: "0.8rem",
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: 2,
              background: "#10b981",
              display: "inline-block",
            }}
          />
          <span style={{ color: "var(--text-secondary)" }}>Voz percibida femenina</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: 2,
              background: "#818cf8",
              display: "inline-block",
            }}
          />
          <span style={{ color: "var(--text-secondary)" }}>Voz percibida masculina</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: 2,
              background: "#f59e0b",
              display: "inline-block",
            }}
          />
          <span style={{ color: "var(--text-secondary)" }}>Indeterminado</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: 2,
              background: "rgba(239, 68, 68, 0.4)",
              border: "1px dashed #ef4444",
              display: "inline-block",
            }}
          />
          <span style={{ color: "var(--text-secondary)" }}>Interrupción / Solapamiento</span>
        </div>
      </div>

      {/* Contenedor desplazable */}
      <div
        style={{
          overflowX: "auto",
          background: "var(--bg-surface-elevated)",
          borderRadius: "var(--radius-md)",
          padding: "1rem 1rem 1.5rem",
          border: "1px solid var(--border-subtle)",
        }}
      >
        <div style={{ minWidth: `${anchoBase}%`, position: "relative" }}>
          {/* Regla temporal superior */}
          <div
            style={{
              position: "relative",
              height: "24px",
              borderBottom: "1px solid var(--border-subtle)",
              marginBottom: "0.75rem",
              fontSize: "0.7rem",
              fontFamily: "var(--font-mono)",
              color: "var(--text-muted)",
            }}
          >
            {marcasTiempo.map((s) => {
              const left = (s / duracionTotal) * 100;
              const min = Math.floor(s / 60);
              const sec = s % 60;
              return (
                <div
                  key={s}
                  style={{
                    position: "absolute",
                    left: `${left}%`,
                    top: 0,
                    transform: "translateX(-50%)",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                  }}
                >
                  <span>{min > 0 ? `${min}m ${sec}s` : `${sec}s`}</span>
                  <div
                    style={{
                      width: "1px",
                      height: "4px",
                      background: "var(--border-subtle)",
                      marginTop: "2px",
                    }}
                  />
                </div>
              );
            })}
          </div>

          {/* Carriles por hablante */}
          {hablantes.map((hab) => {
            const estiloVoz = getEtiquetaColor(hab.etiqueta);
            const turnosHablante = turnos.filter((t) => t.hablante === hab.hablante);

            return (
              <div
                key={hab.hablante}
                style={{
                  display: "flex",
                  alignItems: "center",
                  marginBottom: "0.85rem",
                  gap: "0.75rem",
                }}
              >
                {/* Etiqueta del carril */}
                <div
                  style={{
                    width: "120px",
                    flexShrink: 0,
                    display: "flex",
                    alignItems: "center",
                    gap: "0.4rem",
                    fontSize: "0.85rem",
                    fontWeight: 600,
                  }}
                >
                  <span
                    style={{
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
                      background: estiloVoz.fill,
                    }}
                  />
                  <span>Hablante {hab.hablante}</span>
                </div>

                {/* Pista gráfica */}
                <div
                  style={{
                    flex: 1,
                    height: "36px",
                    background: "rgba(0, 0, 0, 0.25)",
                    borderRadius: "var(--radius-sm)",
                    position: "relative",
                    overflow: "hidden",
                    border: "1px solid rgba(255,255,255,0.03)",
                  }}
                >
                  {/* Bloques de turnos */}
                  {turnosHablante.map((turno, idx) => {
                    const left = (turno.inicio / duracionTotal) * 100;
                    const width = Math.max(((turno.fin - turno.inicio) / duracionTotal) * 100, 0.4);
                    const dur = (turno.fin - turno.inicio).toFixed(1);

                    return (
                      <button
                        type="button"
                        key={`${turno.inicio}-${turno.fin}-${idx}`}
                        onClick={() => {
                          const tramo = tramoDeVoz(turno.inicio, turno.fin, duracion);
                          onPlaySegment(
                            tramo.inicio,
                            tramo.fin,
                            hab.hablante,
                            `Hablante ${hab.hablante} (${dur}s)`,
                          );
                        }}
                        onMouseEnter={() =>
                          setHoveredEvent(
                            `Hablante ${hab.hablante}: ${turno.inicio.toFixed(1)}s - ${turno.fin.toFixed(1)}s (${dur}s)`,
                          )
                        }
                        onMouseLeave={() => setHoveredEvent(null)}
                        style={{
                          position: "absolute",
                          left: `${left}%`,
                          width: `${width}%`,
                          top: "4px",
                          bottom: "4px",
                          background: estiloVoz.bg,
                          border: `1px solid ${estiloVoz.border}`,
                          borderRadius: "4px",
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          padding: 0,
                          transition: "all 0.15s ease",
                        }}
                        title={`Hablante ${hab.hablante}: ${turno.inicio.toFixed(1)}s - ${turno.fin.toFixed(1)}s (${dur}s)`}
                        aria-label={`Reproducir turno de Hablante ${hab.hablante} de ${turno.inicio.toFixed(1)}s a ${turno.fin.toFixed(1)}s`}
                      >
                        {width > 3 && (
                          <Volume2 size={10} color={estiloVoz.fill} style={{ opacity: 0.7 }} />
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}

          {/* Carril de solapamientos e interrupciones detectadas */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              marginTop: "0.5rem",
              paddingTop: "0.5rem",
              borderTop: "1px dashed var(--border-subtle)",
              gap: "0.75rem",
            }}
          >
            <div
              style={{
                width: "120px",
                flexShrink: 0,
                fontSize: "0.75rem",
                color: "var(--solapamiento-exito)",
                fontWeight: 600,
              }}
            >
              Interrupciones ({interrupciones.length})
            </div>

            <div
              style={{
                flex: 1,
                height: "26px",
                background: "rgba(239, 68, 68, 0.05)",
                borderRadius: "var(--radius-sm)",
                position: "relative",
              }}
            >
              {interrupciones.map((inter, idx) => {
                const left = (inter.inicio / duracionTotal) * 100;
                const width = Math.max(((inter.fin - inter.inicio) / duracionTotal) * 100, 0.5);
                const colorTipo =
                  inter.tipo === "con_exito"
                    ? "#ef4444"
                    : inter.tipo === "intento"
                      ? "#f97316"
                      : "#06b6d4";

                return (
                  <button
                    type="button"
                    key={`inter-${inter.inicio}-${idx}`}
                    onClick={() => {
                      const tramo = tramoDeEvento(inter.inicio, inter.fin, duracion);
                      onPlaySegment(
                        tramo.inicio,
                        tramo.fin,
                        inter.interrumpe,
                        `Interrupción: Hablante ${inter.interrumpe} a Hablante ${inter.interrumpido}`,
                      );
                    }}
                    onMouseEnter={() =>
                      setHoveredEvent(
                        `Interrupción ${inter.tipo}: Hablante ${inter.interrumpe} entra sobre Hablante ${inter.interrumpido} en ${inter.inicio.toFixed(1)}s`,
                      )
                    }
                    onMouseLeave={() => setHoveredEvent(null)}
                    style={{
                      position: "absolute",
                      left: `${left}%`,
                      width: `${width}%`,
                      top: "2px",
                      bottom: "2px",
                      background: colorTipo,
                      borderRadius: "3px",
                      cursor: "pointer",
                      padding: 0,
                      border: "none",
                      boxShadow: `0 0 6px ${colorTipo}`,
                    }}
                    title={`Interrupción ${inter.tipo}: Hablante ${inter.interrumpe} -> Hablante ${inter.interrumpido}`}
                    aria-label={`Reproducir interrupción de Hablante ${inter.interrumpe} a Hablante ${inter.interrumpido}`}
                  />
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Tooltip de evento interactivo */}
      <div
        style={{
          marginTop: "0.75rem",
          minHeight: "22px",
          fontSize: "0.8rem",
          color: hoveredEvent ? "var(--accent-primary)" : "var(--text-muted)",
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
        }}
      >
        <span>
          {hoveredEvent || "Pasa el ratón sobre un turno o interrupción para ver detalles."}
        </span>
      </div>
    </div>
  );
};
