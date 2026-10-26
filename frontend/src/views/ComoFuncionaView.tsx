import { BookOpen, FileText, Lock, Scale, Shield, Sliders, VolumeX } from "lucide-react";
import type React from "react";

export const ComoFuncionaView: React.FC = () => {
  return (
    <div style={{ maxWidth: "900px", margin: "0 auto" }}>
      {/* Encabezado */}
      <div style={{ marginBottom: "2.5rem", textAlign: "center" }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
            padding: "0.3rem 0.85rem",
            borderRadius: "var(--radius-full)",
            background: "var(--bg-surface-elevated)",
            color: "var(--accent-primary)",
            fontSize: "0.8rem",
            fontWeight: 700,
            marginBottom: "0.75rem",
            border: "1px solid var(--border-subtle)",
          }}
        >
          <BookOpen size={16} />
          Transparencia y Explicabilidad (RF-22)
        </div>
        <h1 style={{ fontSize: "2rem", fontWeight: 800, marginBottom: "0.5rem" }}>
          Cómo funciona Athenis Voces
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "1rem", lineHeight: 1.6 }}>
          Todo lo que el sistema mide, cómo lo calcula, qué tecnología emplea y cuáles son sus
          límites éticos y técnicos.
        </p>
      </div>

      {/* Los 4 pilares éticos */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "1.25rem",
          marginBottom: "3rem",
        }}
      >
        <div className="card">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.65rem",
              marginBottom: "0.5rem",
            }}
          >
            <VolumeX size={20} color="var(--accent-primary)" />
            <h3 style={{ fontSize: "1rem" }}>Sin transcripción</h3>
          </div>
          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
            El sistema analiza exclusivamente la física de las señales sonoras y sus envolventes de
            frecuencia. Jamás transcribe ni procesa lo que se dice.
          </p>
        </div>

        <div className="card">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.65rem",
              marginBottom: "0.5rem",
            }}
          >
            <Lock size={20} color="var(--accent-primary)" />
            <h3 style={{ fontSize: "1rem" }}>Privacidad local</h3>
          </div>
          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
            El audio no sale del entorno de procesamiento. Los archivos y fragmentos se eliminan
            automáticamente tras 24 horas (RF-23).
          </p>
        </div>

        <div className="card">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.65rem",
              marginBottom: "0.5rem",
            }}
          >
            <Scale size={20} color="var(--accent-primary)" />
            <h3 style={{ fontSize: "1rem" }}>Supervisión humana</h3>
          </div>
          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
            El algoritmo propone; una persona confirma obligatoriamente cada voz presente. Nunca se
            publican métricas automáticas sin supervisión (RN-02).
          </p>
        </div>
      </div>

      {/* Glosario de términos */}
      <div className="card" style={{ marginBottom: "2.5rem" }}>
        <h2
          style={{
            fontSize: "1.25rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            marginBottom: "1.25rem",
          }}
        >
          <FileText size={20} color="var(--accent-primary)" />
          Glosario acústico y conversacional
        </h2>

        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div style={{ paddingBottom: "1rem", borderBottom: "1px solid var(--border-subtle)" }}>
            <div style={{ fontWeight: 700, color: "var(--text-primary)", marginBottom: "0.25rem" }}>
              Turno de habla (RF-05)
            </div>
            <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
              Intervalo continuo de tiempo en el que habla una sola persona sin pisarse con otra.
            </p>
          </div>

          <div style={{ paddingBottom: "1rem", borderBottom: "1px solid var(--border-subtle)" }}>
            <div style={{ fontWeight: 700, color: "var(--text-primary)", marginBottom: "0.25rem" }}>
              Solapamiento (RF-05)
            </div>
            <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
              Tramo en el que dos o más personas hablan al mismo tiempo. Se clasifica según su
              duración y resolución.
            </p>
          </div>

          <div style={{ paddingBottom: "1rem", borderBottom: "1px solid var(--border-subtle)" }}>
            <div style={{ fontWeight: 700, color: "var(--text-primary)", marginBottom: "0.25rem" }}>
              Interrupción con éxito vs Intento vs Señal de escucha (RF-14, RN-07)
            </div>
            <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
              • <strong>Con éxito:</strong> quien estaba hablando se calla en los 2 segundos
              posteriores a que entre la otra voz. Cuenta como interrupción.
              <br />• <strong>Intento:</strong> quien estaba hablando continúa, y quien entra habla
              durante 1 segundo o más. Cuenta como interrupción.
              <br />• <strong>Señal de escucha:</strong> quien entra habla menos de 1 segundo
              («ajá», «sí», «entiendo»). Funciona como retroalimentación positiva y{" "}
              <strong>NO cuenta como interrupción</strong>.
            </p>
          </div>

          <div>
            <div style={{ fontWeight: 700, color: "var(--text-primary)", marginBottom: "0.25rem" }}>
              Voces presentes vs Voces cortas (RN-01, D-15, D-18)
            </div>
            <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
              Solo pasan a la pantalla de confirmación las personas con al menos 10 segundos de
              habla y 3 fragmentos auditables. Las intervenciones breves se agrupan en «voces
              cortas», se muestran aparte y no distorsionan los ratios de grupo.
            </p>
          </div>
        </div>
      </div>

      {/* Fórmulas matemáticas */}
      <div className="card" style={{ marginBottom: "2.5rem" }}>
        <h2
          style={{
            fontSize: "1.25rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            marginBottom: "1.25rem",
          }}
        >
          <Sliders size={20} color="var(--accent-primary)" />
          Fórmulas matemáticas auditables (RN-06)
        </h2>

        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <div
            style={{
              padding: "1rem",
              background: "var(--bg-surface-elevated)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ fontWeight: 700, marginBottom: "0.25rem" }}>
              Ratio de Representación (RR)
            </div>
            <code
              style={{
                fontFamily: "var(--font-mono)",
                color: "var(--accent-primary)",
                display: "block",
                margin: "0.5rem 0",
              }}
            >
              RR = (T_F / T_E) / (N_F / N_E)
            </code>
            <p style={{ fontSize: "0.825rem", color: "var(--text-secondary)" }}>
              Compara la cuota de tiempo femenino con su proporción numérica en la reunión. Si en
              una reunión hay 50% de mujeres pero hablan el 25% del tiempo, el RR es 0.5. Si no hay
              voces femeninas, el resultado es estrictamente «no aplicable» (nunca 0).
            </p>
          </div>

          <div
            style={{
              padding: "1rem",
              background: "var(--bg-surface-elevated)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ fontWeight: 700, marginBottom: "0.25rem" }}>
              Brecha de Interrupción (BI)
            </div>
            <code
              style={{
                fontFamily: "var(--font-mono)",
                color: "var(--accent-primary)",
                display: "block",
                margin: "0.5rem 0",
              }}
            >
              BI = (I_F / (T_F / 600)) / (I_M / (T_M / 600))
            </code>
            <p style={{ fontSize: "0.825rem", color: "var(--text-secondary)" }}>
              Cociente entre la tasa de interrupciones que sufren las voces femeninas por cada 10
              minutos (600 s) y la tasa que sufren las masculinas. Normaliza la medida para que el
              grupo que habla más no parezca artificialmente más interrumpido.
            </p>
          </div>
        </div>
      </div>

      {/* Límites conocidos */}
      <div className="card" style={{ marginBottom: "3rem" }}>
        <h2
          style={{
            fontSize: "1.25rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            marginBottom: "1.25rem",
          }}
        >
          <Shield size={20} color="var(--voz-indeterminado)" />
          Límites declarados y perspectiva ética
        </h2>

        <ul
          style={{
            paddingLeft: "1.25rem",
            color: "var(--text-secondary)",
            fontSize: "0.875rem",
            lineHeight: 1.8,
          }}
        >
          <li>
            <strong>La voz percibida no es la identidad de género:</strong> La acústica tonal
            describe cómo suena una voz en la grabación, nunca define la identidad personal ni de
            género de los participantes.
          </li>
          <li>
            <strong>Solapamientos colaborativos sin palabras:</strong> Al no transcribir el texto,
            no es posible distinguir si una interrupción es competitiva o una muestra entusiasta de
            apoyo y coconstrucción conversacional. Por eso el sistema permite escuchar cada evento
            sonoro.
          </li>
          <li>
            <strong>Categoría «Indeterminado» de primer nivel:</strong> No se fuerza una
            clasificación binaria. Cualquier voz que genere dudas o no pueda determinarse se asigna
            a esta categoría sin repartirse.
          </li>
          <li>
            <strong>Evaluación ciega sobre Corpus AMI:</strong> El pipeline de separación y
            diarización se valida con métricas DER estándar en reuniones de prueba sin sobreajuste.
          </li>
        </ul>
      </div>
    </div>
  );
};
