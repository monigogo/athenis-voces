import { PieChart, Users } from "lucide-react";
import type React from "react";
import type { MetricasGrupo, MetricasHablante } from "../types/contrato";

interface Props {
  grupos: MetricasGrupo[];
  hablantes: MetricasHablante[];
  duracionTotal: number;
}

export const ShareChart: React.FC<Props> = ({ grupos, hablantes }) => {
  const getEtiquetaLabel = (etiqueta: string) => {
    switch (etiqueta) {
      case "femenino":
        return "Voz percibida femenina";
      case "masculino":
        return "Voz percibida masculina";
      default:
        return "Indeterminado";
    }
  };

  const getEtiquetaColor = (etiqueta: string) => {
    switch (etiqueta) {
      case "femenino":
        return "#10b981";
      case "masculino":
        return "#818cf8";
      default:
        return "#f59e0b";
    }
  };

  // Calcular totales para la barra
  const tiempoTotalHabla = grupos.reduce((acc, g) => acc + g.segundos_habla, 0) || 1;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
        gap: "1.5rem",
        marginBottom: "2rem",
      }}
    >
      {/* Cuota por grupo */}
      <div className="card">
        <h3
          style={{
            fontSize: "1.05rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            marginBottom: "1rem",
          }}
        >
          <PieChart size={18} color="var(--accent-primary)" />
          Cuota de tiempo por grupo percibido
        </h3>

        {/* Barra proporcional horizontal */}
        <div
          style={{
            height: "28px",
            borderRadius: "var(--radius-sm)",
            overflow: "hidden",
            display: "flex",
            marginBottom: "1.25rem",
            background: "var(--bg-surface-elevated)",
            border: "1px solid var(--border-subtle)",
          }}
        >
          {grupos.map((g) => {
            const pct = g.cuota_tiempo ?? (g.segundos_habla / tiempoTotalHabla) * 100;
            if (pct <= 0) return null;
            return (
              <div
                key={g.etiqueta}
                style={{
                  width: `${pct}%`,
                  background: getEtiquetaColor(g.etiqueta),
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  color: "#0b0f17",
                  transition: "width 0.3s ease",
                  padding: "0 4px",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
                title={`${getEtiquetaLabel(g.etiqueta)}: ${pct.toFixed(1)}%`}
              >
                {pct > 12 ? `${pct.toFixed(0)}%` : ""}
              </div>
            );
          })}
        </div>

        {/* Tarjetas de desglose por grupo */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {grupos.map((g) => {
            const pct = g.cuota_tiempo ?? (g.segundos_habla / tiempoTotalHabla) * 100;
            const color = getEtiquetaColor(g.etiqueta);

            return (
              <div
                key={g.etiqueta}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.65rem 0.85rem",
                  background: "var(--bg-surface-elevated)",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.65rem" }}>
                  <span style={{ width: 10, height: 10, borderRadius: "50%", background: color }} />
                  <div>
                    <div style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                      {getEtiquetaLabel(g.etiqueta)}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      {g.numero_voces} {g.numero_voces === 1 ? "voz presente" : "voces presentes"} ·{" "}
                      {g.turnos} turnos
                    </div>
                  </div>
                </div>

                <div style={{ textAlign: "right" }}>
                  <div className="mono-num" style={{ fontSize: "0.95rem", fontWeight: 700, color }}>
                    {pct.toFixed(1)}%
                  </div>
                  <div
                    className="mono-num"
                    style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}
                  >
                    {g.segundos_habla.toFixed(1)}s
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tiempo individual por hablante */}
      <div className="card">
        <h3
          style={{
            fontSize: "1.05rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            marginBottom: "1rem",
          }}
        >
          <Users size={18} color="var(--accent-primary)" />
          Distribución individual de intervenciones
        </h3>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
          {hablantes.map((h) => {
            const color = getEtiquetaColor(h.etiqueta);
            const pctHabla = (h.segundos_habla / tiempoTotalHabla) * 100;

            return (
              <div key={h.hablante}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: "0.85rem",
                    marginBottom: "0.35rem",
                  }}
                >
                  <span
                    style={{
                      fontWeight: 600,
                      display: "flex",
                      alignItems: "center",
                      gap: "0.4rem",
                    }}
                  >
                    <span style={{ width: 8, height: 8, borderRadius: "50%", background: color }} />
                    Hablante {h.hablante}
                  </span>
                  <span className="mono-num" style={{ color: "var(--text-secondary)" }}>
                    {h.segundos_habla.toFixed(1)}s ({pctHabla.toFixed(1)}%)
                  </span>
                </div>

                <div
                  style={{
                    height: "8px",
                    background: "var(--bg-surface-elevated)",
                    borderRadius: "4px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${pctHabla}%`,
                      background: color,
                      borderRadius: "4px",
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
