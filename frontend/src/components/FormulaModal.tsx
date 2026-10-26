import { Calculator, Info, X } from "lucide-react";
import type React from "react";

export interface FormulaInfo {
  titulo: string;
  simbolo?: string;
  formula: string;
  definicion: string;
  interpretacion: string;
  variables: { nombre: string; descripcion: string }[];
}

export const DICCIONARIO_FORMULAS: Record<string, FormulaInfo> = {
  ratio_representacion: {
    titulo: "Ratio de Representación (RR)",
    simbolo: "RR",
    formula: "RR = \\frac{T_F / T_E}{N_F / N_E}",
    definicion:
      "Relación entre el porcentaje de tiempo que hablan las voces percibidas como femeninas y la proporción que representan en el número de voces presentes.",
    interpretacion:
      "Un valor igual a 1.0 indica representación proporcional exacta. Menor a 1.0 indica que hablan menos de lo proporcional a su presencia; mayor a 1.0 indica que hablan más.",
    variables: [
      { nombre: "T_F", descripcion: "Segundos de habla de las voces percibidas como femeninas." },
      {
        nombre: "T_E",
        descripcion: "Segundos totales de habla de las voces etiquetadas presentes.",
      },
      { nombre: "N_F", descripcion: "Número de voces percibidas como femeninas." },
      { nombre: "N_E", descripcion: "Número total de voces etiquetadas presentes." },
    ],
  },
  brecha_interrupcion: {
    titulo: "Brecha de Interrupción (BI)",
    simbolo: "BI",
    formula: "BI = \\frac{I_F / (T_F / 600)}{I_M / (T_M / 600)}",
    definicion:
      "Compara la tasa de interrupciones recibidas por cada 10 minutos (600 s) de habla entre el grupo femenino y el grupo masculino.",
    interpretacion:
      "Un valor superior a 1.0 indica que las voces percibidas como femeninas son interrumpidas a una frecuencia mayor que las masculinas, normalizado por su tiempo de habla.",
    variables: [
      {
        nombre: "I_F",
        descripcion: "Interrupciones recibidas por las voces femeninas (con éxito o intento).",
      },
      { nombre: "T_F / 600", descripcion: "Bloques de 10 minutos hablados por voces femeninas." },
      { nombre: "I_M", descripcion: "Interrupciones recibidas por las voces masculinas." },
      { nombre: "T_M / 600", descripcion: "Bloques de 10 minutos hablados por voces masculinas." },
    ],
  },
  tasa_interrupcion_recibida: {
    titulo: "Tasa de Interrupción Recibida",
    simbolo: "Tasa",
    formula:
      "\\text{Tasa} = \\frac{\\text{Interrupciones recibidas}}{\\text{Segundos de habla propia} / 600}",
    definicion:
      "Frecuencia con la que una persona o grupo recibe interrupciones, normalizada por cada 10 minutos de habla efectiva.",
    interpretacion:
      "Permite comparar personas o grupos independientemente de cuánto tiempo haya hablado cada uno.",
    variables: [
      {
        nombre: "Interrupciones recibidas",
        descripcion: "Suma de interrupciones con éxito e intentos de interrupción.",
      },
      { nombre: "600 s", descripcion: "10 minutos de conversación." },
    ],
  },
  recupera_palabra: {
    titulo: "Recuperación de la Palabra",
    simbolo: "% Recup.",
    formula:
      "\\% = \\frac{\\text{Interrupciones con éxito donde retoma en } \\le 10\\text{ s}}{\\text{Total de interrupciones con éxito recibidas}} \\times 100",
    definicion:
      "Porcentaje de ocasiones en las que la persona, tras haber sido interrumpida con éxito y perder el turno, vuelve a intervenir en 10 segundos o menos.",
    interpretacion:
      "Mide la capacidad de persistencia o reapropiación del turno tras una interrupción.",
    variables: [
      {
        nombre: "10 s",
        descripcion: "Ventana temporal para considerar que se recupera la palabra.",
      },
    ],
  },
  indice_protagonismo: {
    titulo: "Índice de Protagonismo (IP)",
    simbolo: "IP",
    formula:
      "IP = w_t \\cdot \\text{CuotaTiempo} + w_l \\cdot \\text{TurnosLargos} + w_p \\cdot \\text{Posicion}",
    definicion:
      "Medida compuesta que pondera el tiempo de habla, la tenencia de turnos largos de desarrollo (>30 s) y la ocupación de turnos clave (abrir o cerrar el episodio).",
    interpretacion:
      "Puntuación entre 0 y 100 que resume el liderazgo conversacional objetivo sin juicios de valor.",
    variables: [
      { nombre: "Cuota de tiempo", descripcion: "% de habla sobre el total de la reunión." },
      { nombre: "Turnos largos", descripcion: "Intervenciones sin interrupción de más de 30 s." },
      {
        nombre: "Posición",
        descripcion: "Si tiene el primer turno > 5 s (abre) o el último > 5 s (cierra).",
      },
    ],
  },
};

interface Props {
  formulaKey: string | null;
  onClose: () => void;
}

export const FormulaModal: React.FC<Props> = ({ formulaKey, onClose }) => {
  if (!formulaKey) return null;
  const info = DICCIONARIO_FORMULAS[formulaKey] || {
    titulo: "Fórmula de la métrica",
    formula: formulaKey,
    definicion: "Esta métrica describe un parámetro acústico y temporal del episodio analizado.",
    interpretacion: "Consulte la sección 'Cómo funciona' para el desglose detallado.",
    variables: [],
  };

  return (
    <div
      className="modal-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={onClose} aria-label="Cerrar modal">
          <X size={20} />
        </button>

        <div
          style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: "var(--radius-md)",
              background: "var(--bg-surface-elevated)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--accent-primary)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <Calculator size={20} />
          </div>
          <div>
            <h2 id="modal-title" style={{ fontSize: "1.25rem" }}>
              {info.titulo}
            </h2>
            <span
              style={{
                fontSize: "0.75rem",
                color: "var(--text-muted)",
                textTransform: "uppercase",
              }}
            >
              Principio Explicable (RN-06)
            </span>
          </div>
        </div>

        <div
          style={{
            background: "var(--bg-surface-elevated)",
            padding: "1rem 1.25rem",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--border-subtle)",
            fontFamily: "var(--font-mono)",
            fontSize: "1.05rem",
            color: "var(--accent-primary)",
            textAlign: "center",
            marginBottom: "1.25rem",
            letterSpacing: "0.02em",
          }}
        >
          {info.formula}
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <h4
            style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "0.35rem" }}
          >
            Definición técnica
          </h4>
          <p style={{ fontSize: "0.9rem", color: "var(--text-primary)", lineHeight: 1.6 }}>
            {info.definicion}
          </p>
        </div>

        <div style={{ marginBottom: "1.25rem" }}>
          <h4
            style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "0.35rem" }}
          >
            Cómo interpretarlo
          </h4>
          <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
            {info.interpretacion}
          </p>
        </div>

        {info.variables.length > 0 && (
          <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "1rem" }}>
            <h4
              style={{
                fontSize: "0.8rem",
                color: "var(--text-muted)",
                marginBottom: "0.5rem",
                textTransform: "uppercase",
              }}
            >
              Variables que intervienen
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {info.variables.map((v) => (
                <div
                  key={v.nombre}
                  style={{ display: "flex", gap: "0.75rem", fontSize: "0.85rem" }}
                >
                  <code
                    style={{
                      fontFamily: "var(--font-mono)",
                      color: "var(--accent-primary)",
                      fontWeight: 600,
                      minWidth: "60px",
                    }}
                  >
                    {v.nombre}
                  </code>
                  <span style={{ color: "var(--text-secondary)" }}>{v.descripcion}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div
          style={{
            marginTop: "1.5rem",
            padding: "0.75rem",
            borderRadius: "var(--radius-sm)",
            background: "rgba(255,255,255,0.03)",
            fontSize: "0.75rem",
            color: "var(--text-muted)",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
          }}
        >
          <Info size={16} />
          <span>
            Athenis Voces calcula todas las métricas acústicas de forma auditable y sin
            transcripción de texto.
          </span>
        </div>
      </div>
    </div>
  );
};
