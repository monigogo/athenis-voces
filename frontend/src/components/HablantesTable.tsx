import { HelpCircle, UserCheck } from "lucide-react";
import type React from "react";
import type { MetricasHablante } from "../types/contrato";

interface Props {
  hablantes: MetricasHablante[];
  onOpenFormula: (clave: string) => void;
}

export const HablantesTable: React.FC<Props> = ({ hablantes, onOpenFormula }) => {
  const getEtiquetaBadge = (etiqueta: string) => {
    switch (etiqueta) {
      case "femenino":
        return {
          clase: "badge-voz femenina",
          label: "Voz percibida femenina",
        };
      case "masculino":
        return {
          clase: "badge-voz masculina",
          label: "Voz percibida masculina",
        };
      default:
        return {
          clase: "badge-voz indeterminado",
          label: "Indeterminado",
        };
    }
  };

  return (
    <div className="card" style={{ marginBottom: "2rem" }}>
      <div style={{ marginBottom: "1.25rem" }}>
        <h3 style={{ fontSize: "1.1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <UserCheck size={18} color="var(--accent-primary)" />
          Métricas individuales por hablante
        </h3>
        <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
          Datos objetivos de la conversación sin rankings ni calificaciones personales (8.3, RN-10).
          Haz clic en los títulos para ver la fórmula.
        </p>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Hablante</th>
              <th>Voz percibida</th>
              <th>Origen</th>
              <th>
                <button
                  type="button"
                  onClick={() => onOpenFormula("tasa_interrupcion_recibida")}
                  style={{
                    background: "none",
                    border: "none",
                    color: "inherit",
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.25rem",
                    font: "inherit",
                    fontWeight: "inherit",
                  }}
                >
                  Tiempo habla <HelpCircle size={12} />
                </button>
              </th>
              <th>Turnos / Largos</th>
              <th>Posición</th>
              <th>Interrupciones (rec / hechas)</th>
              <th>
                <button
                  type="button"
                  onClick={() => onOpenFormula("tasa_interrupcion_recibida")}
                  style={{
                    background: "none",
                    border: "none",
                    color: "inherit",
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.25rem",
                    font: "inherit",
                    fontWeight: "inherit",
                  }}
                >
                  Tasa / 10m <HelpCircle size={12} />
                </button>
              </th>
              <th>
                <button
                  type="button"
                  onClick={() => onOpenFormula("recupera_palabra")}
                  style={{
                    background: "none",
                    border: "none",
                    color: "inherit",
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.25rem",
                    font: "inherit",
                    fontWeight: "inherit",
                  }}
                >
                  Recup. palabra <HelpCircle size={12} />
                </button>
              </th>
              <th>
                <button
                  type="button"
                  onClick={() => onOpenFormula("indice_protagonismo")}
                  style={{
                    background: "none",
                    border: "none",
                    color: "inherit",
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.25rem",
                    font: "inherit",
                    fontWeight: "inherit",
                  }}
                >
                  Protagonismo <HelpCircle size={12} />
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {hablantes.map((h) => {
              const badge = getEtiquetaBadge(h.etiqueta);
              return (
                <tr key={h.hablante}>
                  <td style={{ fontWeight: 700 }}>Hablante {h.hablante}</td>
                  <td>
                    <span className={badge.clase}>{badge.label}</span>
                  </td>
                  <td>
                    <span
                      style={{
                        fontSize: "0.75rem",
                        padding: "0.2rem 0.5rem",
                        borderRadius: "var(--radius-sm)",
                        background: "var(--bg-surface-elevated)",
                        color: "var(--text-secondary)",
                        border: "1px solid var(--border-subtle)",
                      }}
                    >
                      {h.origen === "modelo" ? "Propuesta modelo" : "Asignada persona"}
                    </span>
                  </td>
                  <td className="mono-num" style={{ fontWeight: 600 }}>
                    {h.segundos_habla.toFixed(1)}s
                  </td>
                  <td className="mono-num">
                    {h.turnos} turnos ({h.turnos_largos} &gt;30s)
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: "0.35rem" }}>
                      {h.abre && (
                        <span
                          style={{
                            fontSize: "0.7rem",
                            background: "rgba(45, 212, 191, 0.15)",
                            color: "var(--accent-primary)",
                            padding: "0.15rem 0.4rem",
                            borderRadius: "3px",
                          }}
                        >
                          Abre
                        </span>
                      )}
                      {h.cierra && (
                        <span
                          style={{
                            fontSize: "0.7rem",
                            background: "rgba(129, 140, 248, 0.15)",
                            color: "#818cf8",
                            padding: "0.15rem 0.4rem",
                            borderRadius: "3px",
                          }}
                        >
                          Cierra
                        </span>
                      )}
                      {!h.abre && !h.cierra && (
                        <span style={{ color: "var(--text-muted)" }}>—</span>
                      )}
                    </div>
                  </td>
                  <td className="mono-num">
                    <span style={{ color: "#ef4444" }}>{h.interrupciones_recibidas}</span>
                    <span style={{ color: "var(--text-muted)" }}> / </span>
                    <span style={{ color: "#10b981" }}>{h.interrupciones_hechas}</span>
                  </td>
                  <td className="mono-num">
                    {h.tasa_interrupcion_recibida !== null ? (
                      h.tasa_interrupcion_recibida.toFixed(1)
                    ) : (
                      <span style={{ color: "var(--text-muted)" }}>no aplicable</span>
                    )}
                  </td>
                  <td className="mono-num">
                    {h.recupera_palabra !== null ? (
                      `${h.recupera_palabra.toFixed(0)}%`
                    ) : (
                      <span style={{ color: "var(--text-muted)" }}>no aplicable</span>
                    )}
                  </td>
                  <td className="mono-num">
                    {h.indice_protagonismo !== null ? (
                      <span
                        style={{
                          fontWeight: 700,
                          color: "var(--text-primary)",
                          background: "var(--bg-surface-elevated)",
                          padding: "0.2rem 0.5rem",
                          borderRadius: "4px",
                        }}
                      >
                        {h.indice_protagonismo.toFixed(1)}
                      </span>
                    ) : (
                      <span style={{ color: "var(--text-muted)" }}>—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
