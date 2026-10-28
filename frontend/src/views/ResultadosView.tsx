import {
  BarChart3,
  Clock,
  Download,
  HelpCircle,
  Info,
  Mic,
  RotateCcw,
  TrendingUp,
  UserCheck,
  Users,
} from "lucide-react";
import type React from "react";
import { useState } from "react";
import { FormulaModal } from "../components/FormulaModal";
import { HablantesTable } from "../components/HablantesTable";
import { InterrupcionesTable } from "../components/InterrupcionesTable";
import { ShareChart } from "../components/ShareChart";
import { Timeline } from "../components/Timeline";
import { type Resultado, formatearSegundos } from "../types/contrato";

interface Props {
  resultado: Resultado;
  onNuevoAnalisis: () => void;
  onPlayAudio: (inicio: number, fin: number, hablante?: number, titulo?: string) => void;
}

export const ResultadosView: React.FC<Props> = ({ resultado, onNuevoAnalisis, onPlayAudio }) => {
  const [modalFormulaKey, setModalFormulaKey] = useState<string | null>(null);

  // Extraer índices clave
  const indiceRR = resultado.indices.find((i) => i.nombre === "ratio_representacion");
  const indiceBI = resultado.indices.find((i) => i.nombre === "brecha_interrupcion");

  // Descargar JSON del resultado
  const descargarJSON = () => {
    const dataStr = `data:text/json;charset=utf-8,${encodeURIComponent(
      JSON.stringify(resultado, null, 2),
    )}`;
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `${resultado.id_analisis}_resultado.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div>
      {/* Aviso ético obligatorio de la sección 8.4 */}
      <div className="notice-box">
        <Info size={20} color="var(--accent-primary)" style={{ flexShrink: 0, marginTop: "2px" }} />
        <div>
          <strong>Principio de perspectiva de género y anonimato (8.3, 8.4):</strong>
          <p style={{ marginTop: "0.25rem" }}>
            «Estos datos describen este episodio, no a las personas. La voz percibida no es la
            identidad de género.»
          </p>
        </div>
      </div>

      {/* Cabecera del episodio */}
      <div
        className="card"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "2rem",
          flexWrap: "wrap",
          gap: "1.25rem",
          background: "linear-gradient(135deg, rgba(18, 24, 36, 0.9), rgba(26, 35, 50, 0.8))",
        }}
      >
        <div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              marginBottom: "0.35rem",
            }}
          >
            <span className="brand-tag">ID: {resultado.id_analisis}</span>
            <span className="brand-tag">Contrato v{resultado.version_contrato}</span>
          </div>
          <h2 style={{ fontSize: "1.5rem", fontWeight: 800 }}>Resultados del análisis acústico</h2>
          <div
            style={{
              display: "flex",
              gap: "1.25rem",
              fontSize: "0.85rem",
              color: "var(--text-secondary)",
              marginTop: "0.35rem",
            }}
          >
            <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
              <Clock size={14} /> Duración: {formatearSegundos(resultado.duracion)}
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
              <Users size={14} /> {resultado.hablantes.length} voces presentes
            </span>
            {resultado.segundos_voces_cortas > 0 && (
              <span
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.35rem",
                  color: "var(--text-muted)",
                }}
              >
                <Mic size={14} /> {resultado.segundos_voces_cortas.toFixed(1)}s voces cortas (no
                cuentan como voz)
              </span>
            )}
          </div>
        </div>

        <div style={{ display: "flex", gap: "0.75rem" }}>
          <button
            onClick={descargarJSON}
            className="btn btn-secondary"
            title="Descargar resultado JSON (Contrato 0.2)"
          >
            <Download size={16} /> Exportar JSON
          </button>
          <button onClick={onNuevoAnalisis} className="btn btn-primary">
            <RotateCcw size={16} /> Analizar otro audio
          </button>
        </div>
      </div>

      {/* Tarjetas KPI de índices principales (RF-16, RF-17) */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "1.25rem",
          marginBottom: "2rem",
        }}
      >
        {/* Presencia de voz femenina */}
        <div className="card">
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              marginBottom: "0.5rem",
            }}
          >
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 600 }}>
              Presencia femenina (MD-01)
            </span>
            <UserCheck size={18} color="var(--accent-primary)" />
          </div>
          <div style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: "0.35rem" }}>
            {resultado.voz_femenina_presente ? (
              <span style={{ color: "#10b981" }}>Sí</span>
            ) : (
              <span style={{ color: "var(--text-muted)" }}>No</span>
            )}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
            {resultado.voz_femenina_presente && resultado.primera_intervencion_femenina !== null
              ? `Primera intervención a los ${resultado.primera_intervencion_femenina.toFixed(1)}s`
              : "No se identificaron voces percibidas femeninas"}
          </div>
        </div>

        {/* Ratio de Representación (RR) */}
        <div
          className="card"
          onClick={() => setModalFormulaKey("ratio_representacion")}
          style={{ cursor: "pointer" }}
          title="Haz clic para ver fórmula y definición"
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              marginBottom: "0.5rem",
            }}
          >
            <span
              style={{
                fontSize: "0.8rem",
                color: "var(--text-muted)",
                fontWeight: 600,
                display: "flex",
                alignItems: "center",
                gap: "0.25rem",
              }}
            >
              Ratio Representación (RR) <HelpCircle size={14} />
            </span>
            <TrendingUp size={18} color="var(--accent-primary)" />
          </div>

          <div
            style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: "0.35rem" }}
            className="mono-num"
          >
            {indiceRR && indiceRR.valor !== null ? (
              <span style={{ color: indiceRR.valor >= 0.95 ? "#10b981" : "#f59e0b" }}>
                {indiceRR.valor.toFixed(3)}
              </span>
            ) : (
              <span style={{ fontSize: "1.1rem", color: "var(--text-muted)" }}>no aplicable</span>
            )}
          </div>

          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
            {indiceRR && indiceRR.valor !== null
              ? indiceRR.valor >= 1.0
                ? "Tiempo proporcional a la presencia"
                : "Menor tiempo del proporcional a la presencia"
              : "En este episodio no hay voces de este grupo, así que el índice no se puede calcular (8.4)"}
          </div>
        </div>

        {/* Brecha de Interrupción (BI) */}
        <div
          className="card"
          onClick={() => setModalFormulaKey("brecha_interrupcion")}
          style={{ cursor: "pointer" }}
          title="Haz clic para ver fórmula y definición"
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              marginBottom: "0.5rem",
            }}
          >
            <span
              style={{
                fontSize: "0.8rem",
                color: "var(--text-muted)",
                fontWeight: 600,
                display: "flex",
                alignItems: "center",
                gap: "0.25rem",
              }}
            >
              Brecha Interrupción (BI) <HelpCircle size={14} />
            </span>
            <BarChart3 size={18} color="var(--accent-primary)" />
          </div>

          <div
            style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: "0.35rem" }}
            className="mono-num"
          >
            {indiceBI && indiceBI.valor !== null ? (
              <span style={{ color: indiceBI.valor <= 1.1 ? "#10b981" : "#ef4444" }}>
                {indiceBI.valor.toFixed(3)}
              </span>
            ) : (
              <span style={{ fontSize: "1.1rem", color: "var(--text-muted)" }}>no aplicable</span>
            )}
          </div>

          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
            {indiceBI && indiceBI.valor !== null
              ? indiceBI.valor > 1.0
                ? "Las voces femeninas reciben más interrupciones por minuto"
                : "Interrupciones equilibradas entre grupos"
              : "En este episodio no hay voces de este grupo, así que el índice no se puede calcular (8.4)"}
          </div>
        </div>
      </div>

      {/* Línea de tiempo interactiva (RF-17) */}
      <Timeline
        duracion={resultado.duracion}
        hablantes={resultado.hablantes}
        turnos={resultado.turnos}
        solapamientos={resultado.solapamientos}
        interrupciones={resultado.interrupciones}
        onPlaySegment={onPlayAudio}
      />

      {/* Distribución y cuotas */}
      <ShareChart
        grupos={resultado.grupos}
        hablantes={resultado.hablantes}
        duracionTotal={resultado.duracion}
      />

      {/* Tabla de interrupciones con "escuchar" (RF-18, Must) */}
      <InterrupcionesTable
        interrupciones={resultado.interrupciones}
        duracion={resultado.duracion}
        onPlay={(inicio, fin, hablante, titulo) => onPlayAudio(inicio, fin, hablante, titulo)}
      />

      {/* Tabla detallada de hablantes */}
      <HablantesTable
        hablantes={resultado.hablantes}
        onOpenFormula={(clave) => setModalFormulaKey(clave)}
      />

      {/* Modal interactivo de explicabilidad (RN-06, 8.3) */}
      <FormulaModal formulaKey={modalFormulaKey} onClose={() => setModalFormulaKey(null)} />
    </div>
  );
};
