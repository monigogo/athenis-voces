import {
  AlertTriangle,
  BarChart3,
  BookOpen,
  Brain,
  Cpu,
  Ear,
  Eye,
  Fingerprint,
  Heart,
  Layers,
  Mic,
  RefreshCw,
  Shield,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";
import type React from "react";

export const MetodologiaView: React.FC = () => {
  return (
    <div style={{ maxWidth: "960px", margin: "0 auto" }}>
      {/* Encabezado */}
      <div style={{ marginBottom: "3rem", textAlign: "center" }}>
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
          Metodología
        </div>
        <h1
          style={{
            fontSize: "2.25rem",
            fontWeight: 800,
            marginBottom: "0.65rem",
            letterSpacing: "-0.02em",
          }}
        >
          Nuestra metodología
        </h1>
        <p
          style={{
            color: "var(--text-secondary)",
            fontSize: "1.05rem",
            lineHeight: 1.7,
            maxWidth: "650px",
            margin: "0 auto",
          }}
        >
          Cómo funciona Athenis Voces, qué tecnología emplea, cómo se entrenan los modelos y qué
          principios éticos guían cada decisión de diseño.
        </p>
      </div>

      {/* ================================================================== */}
      {/* SECCIÓN 1: ¿Qué es Athenis? */}
      {/* ================================================================== */}
      <section style={{ marginBottom: "3.5rem" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.65rem",
            marginBottom: "1.5rem",
          }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: "var(--radius-md)",
              background: "linear-gradient(135deg, #14b8a6, #2dd4bf)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#0b0f17",
              boxShadow: "0 2px 8px var(--accent-glow)",
              flexShrink: 0,
            }}
          >
            <Sparkles size={18} />
          </div>
          <h2 style={{ fontSize: "1.5rem", fontWeight: 800 }}>¿Qué es Athenis?</h2>
        </div>

        <div className="card" style={{ marginBottom: "1.5rem", padding: "1.75rem" }}>
          <p
            style={{
              color: "var(--text-secondary)",
              fontSize: "0.95rem",
              lineHeight: 1.8,
              marginBottom: "1.25rem",
            }}
          >
            <strong style={{ color: "var(--text-primary)" }}>Athenis Voces</strong> es una
            herramienta de código abierto que mide la{" "}
            <strong style={{ color: "var(--accent-primary)" }}>
              presencia y el protagonismo de las voces femeninas
            </strong>{" "}
            en grabaciones de audio. Analiza exclusivamente la señal de voz —sin transcribir ni
            identificar a nadie— y responde a tres preguntas clave:
          </p>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "1rem",
              marginBottom: "1.25rem",
            }}
          >
            <div
              style={{
                padding: "1.15rem",
                background: "var(--bg-surface-elevated)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  marginBottom: "0.4rem",
                }}
              >
                <Mic size={16} color="var(--voz-femenina)" />
                <span
                  style={{
                    fontWeight: 700,
                    fontSize: "0.875rem",
                    color: "var(--voz-femenina)",
                  }}
                >
                  Presencia
                </span>
              </div>
              <p
                style={{
                  fontSize: "0.825rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.5,
                }}
              >
                ¿Hay voces femeninas en la conversación? ¿Cuántas?
              </p>
            </div>

            <div
              style={{
                padding: "1.15rem",
                background: "var(--bg-surface-elevated)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  marginBottom: "0.4rem",
                }}
              >
                <BarChart3 size={16} color="var(--voz-masculina)" />
                <span
                  style={{
                    fontWeight: 700,
                    fontSize: "0.875rem",
                    color: "var(--voz-masculina)",
                  }}
                >
                  Participación
                </span>
              </div>
              <p
                style={{
                  fontSize: "0.825rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.5,
                }}
              >
                ¿Qué papel ocupan en la conversación? ¿Cuánto tiempo hablan?
              </p>
            </div>

            <div
              style={{
                padding: "1.15rem",
                background: "var(--bg-surface-elevated)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  marginBottom: "0.4rem",
                }}
              >
                <AlertTriangle size={16} color="var(--voz-indeterminado)" />
                <span
                  style={{
                    fontWeight: 700,
                    fontSize: "0.875rem",
                    color: "var(--voz-indeterminado)",
                  }}
                >
                  Respeto del turno
                </span>
              </div>
              <p
                style={{
                  fontSize: "0.825rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.5,
                }}
              >
                ¿Se las interrumpe más que a las voces masculinas?
              </p>
            </div>
          </div>

          <p
            style={{
              color: "var(--text-secondary)",
              fontSize: "0.875rem",
              lineHeight: 1.7,
            }}
          >
            Desarrollado para el reto <em>Mujeres por la IA Abierta</em>, dentro de la Comunidad IA
            de Código Abierto (SEDIA). El sistema calcula cuatro dimensiones a partir de la señal de
            voz: presencia, participación (cuota de tiempo y turnos), posición (quién abre y cierra)
            y respeto del turno (interrupciones recibidas y hechas).
          </p>
        </div>

        {/* Qué NO hace */}
        <div
          className="card"
          style={{
            borderLeftColor: "var(--voz-indeterminado)",
            borderLeftWidth: "4px",
            padding: "1.25rem 1.5rem",
          }}
        >
          <h3
            style={{
              fontSize: "1rem",
              fontWeight: 700,
              marginBottom: "0.75rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <Shield size={18} color="var(--voz-indeterminado)" />
            Lo que Athenis NO hace
          </h3>
          <ul
            style={{
              paddingLeft: "1.25rem",
              color: "var(--text-secondary)",
              fontSize: "0.85rem",
              lineHeight: 1.8,
            }}
          >
            <li>No transcribe ni analiza el contenido de lo que se dice.</li>
            <li>No identifica a las personas por su nombre ni por su voz.</li>
            <li>No infiere identidad de género, edad ni origen a partir de la voz.</li>
            <li>No evalúa ni puntúa a personas concretas.</li>
          </ul>
        </div>
      </section>

      {/* ================================================================== */}
      {/* SECCIÓN 2: ¿Cómo hemos entrenado a los modelos? */}
      {/* ================================================================== */}
      <section style={{ marginBottom: "3.5rem" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.65rem",
            marginBottom: "1.5rem",
          }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: "var(--radius-md)",
              background: "linear-gradient(135deg, #818cf8, #a78bfa)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#0b0f17",
              boxShadow: "0 2px 8px rgba(129, 140, 248, 0.25)",
              flexShrink: 0,
            }}
          >
            <Brain size={18} />
          </div>
          <h2 style={{ fontSize: "1.5rem", fontWeight: 800 }}>
            ¿Cómo hemos entrenado a los modelos?
          </h2>
        </div>

        {/* Pipeline visual */}
        <div className="card" style={{ marginBottom: "1.5rem", padding: "1.75rem" }}>
          <h3
            style={{
              fontSize: "1.1rem",
              fontWeight: 700,
              marginBottom: "1.25rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <Layers size={18} color="var(--accent-primary)" />
            El pipeline de análisis
          </h3>
          <p
            style={{
              color: "var(--text-secondary)",
              fontSize: "0.875rem",
              lineHeight: 1.7,
              marginBottom: "1.5rem",
            }}
          >
            Athenis Voces utiliza dos modelos de inteligencia artificial pre-entrenados, combinados
            en un pipeline de cuatro fases. No hemos re-entrenado los modelos desde cero, sino que
            usamos modelos abiertos existentes y los evaluamos rigurosamente con datos reales:
          </p>

          {/* Los 4 pasos */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0" }}>
            {/* Paso 1 */}
            <div style={{ display: "flex", gap: "1rem", alignItems: "stretch" }}>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  minWidth: "44px",
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: "50%",
                    background: "var(--accent-primary)",
                    color: "#0b0f17",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 800,
                    fontSize: "0.95rem",
                    flexShrink: 0,
                  }}
                >
                  1
                </div>
                <div
                  style={{
                    flex: 1,
                    width: "2px",
                    background: "var(--border-subtle)",
                    margin: "0.5rem 0",
                  }}
                />
              </div>
              <div style={{ paddingBottom: "1.75rem" }}>
                <div
                  style={{
                    fontWeight: 700,
                    fontSize: "1rem",
                    marginBottom: "0.3rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  <Zap size={16} color="var(--accent-primary)" />
                  Preparación del audio
                </div>
                <p
                  style={{
                    fontSize: "0.85rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.6,
                  }}
                >
                  El audio se convierte a WAV mono a 16 kHz mediante{" "}
                  <strong style={{ color: "var(--text-primary)" }}>ffmpeg</strong>. Esto estandariza
                  cualquier formato de entrada para que los modelos trabajen siempre con la misma
                  señal.
                </p>
              </div>
            </div>

            {/* Paso 2 */}
            <div style={{ display: "flex", gap: "1rem", alignItems: "stretch" }}>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  minWidth: "44px",
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: "50%",
                    background: "var(--accent-primary)",
                    color: "#0b0f17",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 800,
                    fontSize: "0.95rem",
                    flexShrink: 0,
                  }}
                >
                  2
                </div>
                <div
                  style={{
                    flex: 1,
                    width: "2px",
                    background: "var(--border-subtle)",
                    margin: "0.5rem 0",
                  }}
                />
              </div>
              <div style={{ paddingBottom: "1.75rem" }}>
                <div
                  style={{
                    fontWeight: 700,
                    fontSize: "1rem",
                    marginBottom: "0.3rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  <Users size={16} color="var(--voz-masculina)" />
                  Diarización (separación de voces)
                </div>
                <p
                  style={{
                    fontSize: "0.85rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.6,
                  }}
                >
                  El modelo{" "}
                  <strong style={{ color: "var(--text-primary)" }}>
                    pyannote/speaker-diarization
                  </strong>{" "}
                  (licencia CC BY 4.0) analiza la señal acústica y separa las voces, asignando a
                  cada persona un número: <em>Hablante 1, Hablante 2, Hablante 3…</em> El modelo
                  identifica cuándo habla cada uno y detecta los solapamientos donde dos o más
                  hablan a la vez. No reconoce identidades: solo agrupa fragmentos de la misma voz.
                </p>
              </div>
            </div>

            {/* Paso 3 */}
            <div style={{ display: "flex", gap: "1rem", alignItems: "stretch" }}>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  minWidth: "44px",
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: "50%",
                    background: "var(--accent-primary)",
                    color: "#0b0f17",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 800,
                    fontSize: "0.95rem",
                    flexShrink: 0,
                  }}
                >
                  3
                </div>
                <div
                  style={{
                    flex: 1,
                    width: "2px",
                    background: "var(--border-subtle)",
                    margin: "0.5rem 0",
                  }}
                />
              </div>
              <div style={{ paddingBottom: "1.75rem" }}>
                <div
                  style={{
                    fontWeight: 700,
                    fontSize: "1rem",
                    marginBottom: "0.3rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  <Ear size={16} color="var(--voz-femenina)" />
                  Propuesta de voz percibida
                </div>
                <p
                  style={{
                    fontSize: "0.85rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.6,
                  }}
                >
                  El modelo{" "}
                  <strong style={{ color: "var(--text-primary)" }}>inaSpeechSegmenter</strong>{" "}
                  analiza las frecuencias tonales de cada voz y <em>propone</em> si suena femenina,
                  masculina o indeterminada. Es una propuesta basada en acústica, no una
                  clasificación definitiva. Se calcula la proporción de tiempo que el modelo detecta
                  como «femenino» o «masculino» en los segmentos limpios de cada hablante, y si cae
                  en una zona intermedia se etiqueta como «indeterminado».
                </p>
              </div>
            </div>

            {/* Paso 4 */}
            <div style={{ display: "flex", gap: "1rem", alignItems: "stretch" }}>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  minWidth: "44px",
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: "50%",
                    background: "var(--accent-primary)",
                    color: "#0b0f17",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 800,
                    fontSize: "0.95rem",
                    flexShrink: 0,
                  }}
                >
                  4
                </div>
                <div
                  style={{
                    flex: 1,
                    width: "2px",
                    background: "transparent",
                    margin: "0.5rem 0",
                  }}
                />
              </div>
              <div style={{ paddingBottom: "0.5rem" }}>
                <div
                  style={{
                    fontWeight: 700,
                    fontSize: "1rem",
                    marginBottom: "0.3rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  <Eye size={16} color="var(--voz-indeterminado)" />
                  Confirmación humana obligatoria
                </div>
                <p
                  style={{
                    fontSize: "0.85rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.6,
                  }}
                >
                  Una persona escucha fragmentos de cada voz y{" "}
                  <strong style={{ color: "var(--text-primary)" }}>confirma o corrige</strong> la
                  propuesta del modelo. Puede aceptar la sugerencia, cambiarla o marcar
                  «indeterminado». Solo después de esta supervisión el sistema calcula las métricas
                  finales. Nunca se publican resultados automáticos sin confirmación humana.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Modelos utilizados */}
        <div className="card" style={{ marginBottom: "1.5rem", padding: "1.75rem" }}>
          <h3
            style={{
              fontSize: "1.1rem",
              fontWeight: 700,
              marginBottom: "1rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <Cpu size={18} color="var(--accent-primary)" />
            Modelos de IA utilizados
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div
              style={{
                padding: "1.15rem",
                background: "var(--bg-surface-elevated)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  fontWeight: 700,
                  marginBottom: "0.25rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <span style={{ color: "var(--voz-masculina)" }}>●</span>
                pyannote/speaker-diarization
              </div>
              <p
                style={{
                  fontSize: "0.825rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.6,
                }}
              >
                Modelo de código abierto (CC BY 4.0) para separar voces en un audio. Asigna un
                número a cada persona hablante y marca cuándo empieza y termina cada turno. Se
                evalúa con la métrica DER (Diarization Error Rate) sobre el corpus AMI.
              </p>
            </div>

            <div
              style={{
                padding: "1.15rem",
                background: "var(--bg-surface-elevated)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  fontWeight: 700,
                  marginBottom: "0.25rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <span style={{ color: "var(--voz-femenina)" }}>●</span>
                inaSpeechSegmenter
              </div>
              <p
                style={{
                  fontSize: "0.825rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.6,
                }}
              >
                Clasificador acústico que segmenta el audio en tramos de voz femenina, masculina y
                ruido/música. Solo analiza las frecuencias del sonido, sin transcribir ni entender
                lo que se dice. Su propuesta es orientativa y siempre requiere confirmación humana.
              </p>
            </div>
          </div>
        </div>

        {/* Evaluación */}
        <div className="card" style={{ padding: "1.75rem" }}>
          <h3
            style={{
              fontSize: "1.1rem",
              fontWeight: 700,
              marginBottom: "1rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <RefreshCw size={18} color="var(--accent-primary)" />
            Evaluación rigurosa
          </h3>
          <p
            style={{
              color: "var(--text-secondary)",
              fontSize: "0.875rem",
              lineHeight: 1.7,
              marginBottom: "1rem",
            }}
          >
            Evaluamos el sistema con datos reales de distintas fuentes. Ninguna salida se usa para
            ajustar el modelo (constitución, regla 9):
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: "1rem",
            }}
          >
            <div
              style={{
                padding: "1rem",
                background: "var(--bg-surface-elevated)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  fontWeight: 700,
                  fontSize: "0.85rem",
                  color: "var(--accent-primary)",
                  marginBottom: "0.25rem",
                }}
              >
                Corpus AMI
              </div>
              <p
                style={{
                  fontSize: "0.8rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.5,
                }}
              >
                Reuniones en inglés con anotaciones de referencia. Licencia CC BY 4.0. Se usa para
                medir el DER y la exactitud de la propuesta de voz.
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
              <div
                style={{
                  fontWeight: 700,
                  fontSize: "0.85rem",
                  color: "var(--accent-primary)",
                  marginBottom: "0.25rem",
                }}
              >
                Grabaciones propias
              </div>
              <p
                style={{
                  fontSize: "0.8rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.5,
                }}
              >
                Conversaciones en español con consentimiento escrito. Dos anotadoras etiquetan las
                interrupciones de forma independiente para medir el acuerdo (kappa).
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ================================================================== */}
      {/* SECCIÓN 3: Ética */}
      {/* ================================================================== */}
      <section style={{ marginBottom: "3rem" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.65rem",
            marginBottom: "1.5rem",
          }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: "var(--radius-md)",
              background: "linear-gradient(135deg, #10b981, #34d399)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#0b0f17",
              boxShadow: "0 2px 8px rgba(16, 185, 129, 0.25)",
              flexShrink: 0,
            }}
          >
            <Heart size={18} />
          </div>
          <h2 style={{ fontSize: "1.5rem", fontWeight: 800 }}>Ética y diseño responsable</h2>
        </div>

        {/* Principio central */}
        <div
          className="notice-box"
          style={{ marginBottom: "1.5rem", fontSize: "0.9rem", lineHeight: 1.7 }}
        >
          <Shield size={20} color="var(--accent-primary)" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <strong>La voz percibida no es la identidad de género.</strong> El sistema no clasifica
            personas ni infiere identidades. Solo describe cómo suena cada voz en la grabación: si
            tiene frecuencias percibidas como femeninas, masculinas o indeterminadas. La identidad
            de cada persona queda fuera del análisis.
          </div>
        </div>

        {/* Cómo etiquetamos */}
        <div className="card" style={{ marginBottom: "1.5rem", padding: "1.75rem" }}>
          <h3
            style={{
              fontSize: "1.1rem",
              fontWeight: 700,
              marginBottom: "1.25rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <Fingerprint size={18} color="var(--accent-primary)" />
            Cómo etiquetamos las voces
          </h3>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "1.25rem",
            }}
          >
            <div
              style={{
                paddingBottom: "1.25rem",
                borderBottom: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  fontWeight: 700,
                  color: "var(--text-primary)",
                  marginBottom: "0.35rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <span className="badge-voz femenina">Persona A</span>
                <span className="badge-voz masculina">Persona B</span>
                <span
                  style={{
                    fontSize: "0.85rem",
                    color: "var(--text-secondary)",
                  }}
                >
                  …no «hombre» ni «mujer»
                </span>
              </div>
              <p
                style={{
                  fontSize: "0.85rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.7,
                  marginTop: "0.5rem",
                }}
              >
                Las voces se etiquetan como{" "}
                <strong style={{ color: "var(--text-primary)" }}>
                  Hablante 1, Hablante 2, Hablante 3…
                </strong>{" "}
                por orden de aparición. Nunca se asocian a nombres, identidades de género ni datos
                personales. El número identifica una voz dentro de la grabación, no a una persona.
              </p>
            </div>

            <div
              style={{
                paddingBottom: "1.25rem",
                borderBottom: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  fontWeight: 700,
                  color: "var(--text-primary)",
                  marginBottom: "0.35rem",
                }}
              >
                El modelo solo propone, la persona decide
              </div>
              <p
                style={{
                  fontSize: "0.85rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.7,
                }}
              >
                El clasificador acústico analiza las frecuencias de la señal y <em>sugiere</em> si
                una voz suena femenina o masculina. Esta propuesta{" "}
                <strong style={{ color: "var(--accent-primary)" }}>
                  siempre la confirma una persona
                </strong>
                , escuchando fragmentos reales de cada voz. Puede aceptar, cambiar o marcar como
                «indeterminado». Sin esta confirmación, no se calculan métricas.
              </p>
            </div>

            <div>
              <div
                style={{
                  fontWeight: 700,
                  color: "var(--text-primary)",
                  marginBottom: "0.35rem",
                }}
              >
                «Indeterminado» es una categoría de primer nivel
              </div>
              <p
                style={{
                  fontSize: "0.85rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.7,
                }}
              >
                No se fuerza una clasificación binaria. Si una voz genera dudas o no se puede
                determinar, se asigna a la categoría{" "}
                <span
                  className="badge-voz indeterminado"
                  style={{ fontSize: "0.7rem", padding: "0.15rem 0.45rem" }}
                >
                  INDETERMINADO
                </span>{" "}
                sin repartirse entre los otros grupos. Este tiempo no se ignora: se contabiliza,
                pero no distorsiona la comparación.
              </p>
            </div>
          </div>
        </div>

        {/* Qué calcula */}
        <div className="card" style={{ marginBottom: "1.5rem", padding: "1.75rem" }}>
          <h3
            style={{
              fontSize: "1.1rem",
              fontWeight: 700,
              marginBottom: "1.25rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <BarChart3 size={18} color="var(--accent-primary)" />
            Qué calcula con esas etiquetas
          </h3>

          <p
            style={{
              color: "var(--text-secondary)",
              fontSize: "0.875rem",
              lineHeight: 1.7,
              marginBottom: "1.25rem",
            }}
          >
            Una vez confirmadas las voces, el sistema agrupa los turnos por categoría de voz y
            calcula:
          </p>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "1rem",
            }}
          >
            <div
              style={{
                padding: "1rem",
                background: "var(--bg-surface-elevated)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  fontWeight: 700,
                  fontSize: "0.85rem",
                  color: "var(--voz-femenina)",
                  marginBottom: "0.35rem",
                }}
              >
                ⏱ Cuánto habla cada grupo
              </div>
              <p
                style={{
                  fontSize: "0.8rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.5,
                }}
              >
                Tiempo total, cuota porcentual, número de turnos y turnos largos (más de 30 s) de
                las voces femeninas frente a las masculinas.
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
              <div
                style={{
                  fontWeight: 700,
                  fontSize: "0.85rem",
                  color: "var(--solapamiento-exito)",
                  marginBottom: "0.35rem",
                }}
              >
                🚫 Cuántas veces se interrumpe a cada uno
              </div>
              <p
                style={{
                  fontSize: "0.8rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.5,
                }}
              >
                Interrupciones con éxito, intentos y señales de escucha. La tasa se normaliza por
                cada 10 minutos de habla para comparar con justicia.
              </p>
            </div>
          </div>
        </div>

        {/* Principios éticos */}
        <div className="card" style={{ padding: "1.75rem" }}>
          <h3
            style={{
              fontSize: "1.1rem",
              fontWeight: 700,
              marginBottom: "1.25rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <Shield size={18} color="var(--voz-femenina)" />
            Principios éticos del proyecto
          </h3>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
              gap: "1rem",
            }}
          >
            <div
              style={{
                padding: "1.15rem",
                background: "var(--bg-surface-elevated)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  marginBottom: "0.4rem",
                }}
              >
                <Eye size={16} color="var(--accent-primary)" />
                <span style={{ fontWeight: 700, fontSize: "0.875rem" }}>
                  Supervisión humana obligatoria
                </span>
              </div>
              <p
                style={{
                  fontSize: "0.8rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.5,
                }}
              >
                Ningún resultado se muestra sin que una persona haya confirmado las etiquetas de
                voz. El modelo propone; la persona decide.
              </p>
            </div>

            <div
              style={{
                padding: "1.15rem",
                background: "var(--bg-surface-elevated)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  marginBottom: "0.4rem",
                }}
              >
                <Fingerprint size={16} color="var(--accent-primary)" />
                <span style={{ fontWeight: 700, fontSize: "0.875rem" }}>Sin identificación</span>
              </div>
              <p
                style={{
                  fontSize: "0.8rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.5,
                }}
              >
                La diarización agrupa voces dentro del audio. No identifica a ninguna persona ni
                envía el audio fuera de la infraestructura propia.
              </p>
            </div>

            <div
              style={{
                padding: "1.15rem",
                background: "var(--bg-surface-elevated)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  marginBottom: "0.4rem",
                }}
              >
                <BarChart3 size={16} color="var(--accent-primary)" />
                <span style={{ fontWeight: 700, fontSize: "0.875rem" }}>
                  Sesgo medido, no supuesto
                </span>
              </div>
              <p
                style={{
                  fontSize: "0.8rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.5,
                }}
              >
                El error del clasificador de voz se publica por grupo, con intervalo de confianza.
                Sabemos cuánto se equivoca y lo declaramos.
              </p>
            </div>

            <div
              style={{
                padding: "1.15rem",
                background: "var(--bg-surface-elevated)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  marginBottom: "0.4rem",
                }}
              >
                <Shield size={16} color="var(--accent-primary)" />
                <span style={{ fontWeight: 700, fontSize: "0.875rem" }}>
                  Modo manual disponible
                </span>
              </div>
              <p
                style={{
                  fontSize: "0.8rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.5,
                }}
              >
                Desactiva toda propuesta automática. La persona clasifica cada voz sin sugerencia
                del modelo, reduciendo la exposición legal bajo el Reglamento de IA de la UE.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
