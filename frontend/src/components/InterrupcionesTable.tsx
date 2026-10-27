import { CheckCircle2, Filter, MessageSquare, Play, XCircle } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { tramoDeEvento } from "../services/api";
import type { Interrupcion, TipoSolapamiento } from "../types/contrato";

interface Props {
  interrupciones: Interrupcion[];
  /** Duración del audio, para que el fragmento no pase de ella (RF-18). */
  duracion: number;
  onPlay: (inicio: number, fin: number, hablante: number, titulo: string) => void;
}

export const InterrupcionesTable: React.FC<Props> = ({ interrupciones, duracion, onPlay }) => {
  const [filtroTipo, setFiltroTipo] = useState<string>("todos");

  const eventosFiltrados = interrupciones.filter((i) => {
    if (filtroTipo === "todos") return true;
    if (filtroTipo === "interrupciones") return i.tipo !== "senal_de_escucha";
    return i.tipo === filtroTipo;
  });

  const getTipoBadge = (tipo: TipoSolapamiento) => {
    switch (tipo) {
      case "con_exito":
        return {
          label: "Con éxito",
          clase: "badge-tag",
          bg: "rgba(239, 68, 68, 0.15)",
          color: "#ef4444",
          border: "rgba(239, 68, 68, 0.35)",
          cuenta: "Sí (quita turno)",
        };
      case "intento":
        return {
          label: "Intento",
          clase: "badge-tag",
          bg: "rgba(249, 115, 22, 0.15)",
          color: "#f97316",
          border: "rgba(249, 115, 22, 0.35)",
          cuenta: "Sí (habla ≥ 1s)",
        };
      case "senal_de_escucha":
        return {
          label: "Señal de escucha",
          clase: "badge-tag",
          bg: "rgba(6, 182, 212, 0.15)",
          color: "#06b6d4",
          border: "rgba(6, 182, 212, 0.35)",
          cuenta: "No (apoyo < 1s)",
        };
    }
  };

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
            <MessageSquare size={18} color="var(--accent-primary)" />
            Registro de interrupciones y solapamientos
          </h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Escucha cada evento en su contexto sonoro (RF-18: hasta 1s antes y máximo 15s).
          </p>
        </div>

        {/* Filtros */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Filter size={14} color="var(--text-muted)" />
          <button
            onClick={() => setFiltroTipo("todos")}
            className={`btn btn-sm ${filtroTipo === "todos" ? "btn-primary" : "btn-secondary"}`}
          >
            Todos ({interrupciones.length})
          </button>
          <button
            onClick={() => setFiltroTipo("interrupciones")}
            className={`btn btn-sm ${filtroTipo === "interrupciones" ? "btn-primary" : "btn-secondary"}`}
          >
            Solo interrupciones (
            {interrupciones.filter((i) => i.tipo !== "senal_de_escucha").length})
          </button>
          <button
            onClick={() => setFiltroTipo("senal_de_escucha")}
            className={`btn btn-sm ${filtroTipo === "senal_de_escucha" ? "btn-primary" : "btn-secondary"}`}
          >
            Señales de escucha ({interrupciones.filter((i) => i.tipo === "senal_de_escucha").length}
            )
          </button>
        </div>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Momento</th>
              <th>Duración</th>
              <th>Quién entra</th>
              <th>A quién interrumpe</th>
              <th>Tipo de evento</th>
              <th>¿Cuenta como interrupción?</th>
              <th style={{ textAlign: "right" }}>Acción</th>
            </tr>
          </thead>
          <tbody>
            {eventosFiltrados.length === 0 ? (
              <tr>
                <td
                  colSpan={7}
                  style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)" }}
                >
                  No hay eventos que coincidan con el filtro seleccionado.
                </td>
              </tr>
            ) : (
              eventosFiltrados.map((item, idx) => {
                const badge = getTipoBadge(item.tipo);
                const dur = (item.fin - item.inicio).toFixed(2);
                const tramo = tramoDeEvento(item.inicio, item.fin, duracion);

                return (
                  <tr key={`inter-${item.inicio}-${idx}`}>
                    <td className="mono-num">
                      {item.inicio.toFixed(1)}s - {item.fin.toFixed(1)}s
                    </td>
                    <td className="mono-num" style={{ color: "var(--text-secondary)" }}>
                      {dur}s
                    </td>
                    <td>
                      <span style={{ fontWeight: 600 }}>Hablante {item.interrumpe}</span>
                    </td>
                    <td>
                      <span style={{ color: "var(--text-secondary)" }}>
                        Hablante {item.interrumpido}
                      </span>
                    </td>
                    <td>
                      <span
                        style={{
                          display: "inline-block",
                          padding: "0.2rem 0.55rem",
                          borderRadius: "var(--radius-sm)",
                          fontSize: "0.75rem",
                          fontWeight: 700,
                          background: badge.bg,
                          color: badge.color,
                          border: `1px solid ${badge.border}`,
                        }}
                      >
                        {badge.label}
                      </span>
                    </td>
                    <td>
                      <span
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.35rem",
                          fontSize: "0.8rem",
                          color:
                            item.tipo !== "senal_de_escucha"
                              ? "var(--text-primary)"
                              : "var(--text-muted)",
                        }}
                      >
                        {item.tipo !== "senal_de_escucha" ? (
                          <CheckCircle2 size={14} color="#ef4444" />
                        ) : (
                          <XCircle size={14} color="var(--text-muted)" />
                        )}
                        {badge.cuenta}
                      </span>
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <button
                        onClick={() =>
                          onPlay(
                            tramo.inicio,
                            tramo.fin,
                            item.interrumpe,
                            `Interrupción: Hablante ${item.interrumpe} a Hablante ${item.interrumpido}`,
                          )
                        }
                        className="btn btn-secondary btn-sm"
                        style={{ display: "inline-flex", gap: "0.35rem" }}
                        title="Escuchar este evento (máx 15 s)"
                        aria-label={`Escuchar interrupción de Hablante ${item.interrumpe} a Hablante ${item.interrumpido}`}
                      >
                        <Play size={12} />
                        Escuchar
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
