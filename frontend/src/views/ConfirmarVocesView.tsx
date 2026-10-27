import {
  AlertTriangle,
  ArrowRight,
  Check,
  CheckCircle2,
  Play,
  ShieldAlert,
  User,
} from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { api } from "../services/api";
import {
  type Confirmacion,
  type EtiquetaConfirmada,
  type EtiquetaVoz,
  type HablantesParaConfirmar,
  type OrigenEtiqueta,
  type Resultado,
  esPropuestaDudosa,
} from "../types/contrato";

interface Props {
  idAnalisis: string;
  onConfirmacionCompleta: (resultado: Resultado) => void;
  onPlayAudio: (inicio: number, fin: number, hablante: number, titulo: string) => void;
}

export const ConfirmarVocesView: React.FC<Props> = ({
  idAnalisis,
  onConfirmacionCompleta,
  onPlayAudio,
}) => {
  const [datosHablantes, setDatosHablantes] = useState<HablantesParaConfirmar | null>(null);
  const [cargando, setCargando] = useState(true);
  const [elecciones, setElecciones] = useState<Record<number, EtiquetaVoz>>({});
  const [enviando, setEnviando] = useState(false);
  const [errorEnvio, setErrorEnvio] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;
    setCargando(true);

    api
      .getHablantes(idAnalisis)
      .then((habs) => {
        if (!cancelado) {
          setDatosHablantes(habs);
          // Ninguna voz sale confirmada: cada una la confirma la persona (RN-02)
          setElecciones({});
          setCargando(false);
        }
      })
      .catch((err) => {
        if (!cancelado) {
          setErrorEnvio(err.message);
          setCargando(false);
        }
      });

    return () => {
      cancelado = true;
    };
  }, [idAnalisis]);

  if (cargando) {
    return (
      <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
        <p style={{ color: "var(--text-secondary)" }}>Cargando hablantes y fragmentos de voz...</p>
      </div>
    );
  }

  if (!datosHablantes) {
    return (
      <div className="card" style={{ textAlign: "center", padding: "3rem", color: "#ef4444" }}>
        <p>No se pudieron obtener las voces de este análisis.</p>
      </div>
    );
  }

  const { hablantes } = datosHablantes;
  const todosConfirmados = hablantes.every((h) => !!elecciones[h.hablante]);
  const faltanPorConfirmar = hablantes.filter((h) => !elecciones[h.hablante]);

  const seleccionarEtiqueta = (hablanteNum: number, etiqueta: EtiquetaVoz) => {
    setElecciones((prev) => ({
      ...prev,
      [hablanteNum]: etiqueta,
    }));
  };

  const handleConfirmar = async () => {
    if (!todosConfirmados) return;
    setEnviando(true);
    setErrorEnvio(null);

    const etiquetasConfirmadas: EtiquetaConfirmada[] = hablantes.map((h) => {
      const elegida = elecciones[h.hablante];
      // Si coincide con la propuesta del modelo -> 'modelo'; en modo manual no hay propuesta -> 'persona'
      const coincidenciaModelo = h.propuesta && h.propuesta.etiqueta === elegida;
      const origen: OrigenEtiqueta = coincidenciaModelo ? "modelo" : "persona";

      return {
        hablante: h.hablante,
        etiqueta: elegida,
        origen,
      };
    });

    const payload: Confirmacion = {
      version_contrato: "0.2",
      etiquetas: etiquetasConfirmadas,
    };

    try {
      const res = await api.enviarConfirmacion(idAnalisis, payload);
      onConfirmacionCompleta(res);
    } catch (err: unknown) {
      setErrorEnvio(err instanceof Error ? err.message : "Error al enviar la confirmación");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div>
      {/* Aviso ético obligatorio de la sección 8.4 */}
      <div className="notice-box warning">
        <ShieldAlert
          size={20}
          color="var(--voz-indeterminado)"
          style={{ flexShrink: 0, marginTop: "2px" }}
        />
        <div>
          <strong>Criterio de supervisión humana (RN-02):</strong>
          <p style={{ marginTop: "0.25rem" }}>
            «El sistema propone cómo suena cada voz; tú decides. Si sabes cómo se presenta
            públicamente esa persona, usa eso. Si no lo sabes, marca ‘indeterminado’.» (Sección 8.4)
          </p>
        </div>
      </div>

      {/* Cabecera (el modo manual se elige antes de subir, RF-08) */}
      <div style={{ marginBottom: "1.75rem" }}>
        <h2 style={{ fontSize: "1.35rem" }}>Confirmación de voces presentes</h2>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
          Solo pasan a confirmación las voces con ≥10 s de habla y ≥3 fragmentos (D-18). Hasta que
          no confirmes todas, no se generarán los resultados (RN-01).
        </p>
      </div>

      {/* Tarjetas de hablantes */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
          gap: "1.5rem",
          marginBottom: "2.5rem",
        }}
      >
        {hablantes.map((h) => {
          const eleccionActual = elecciones[h.hablante];
          const esDudosa = esPropuestaDudosa(h.propuesta);

          return (
            <div
              key={h.hablante}
              className="card"
              style={{
                border: eleccionActual
                  ? "1px solid rgba(45, 212, 191, 0.4)"
                  : "1px solid var(--border-subtle)",
                position: "relative",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  marginBottom: "1rem",
                }}
              >
                <div>
                  <h3
                    style={{
                      fontSize: "1.1rem",
                      fontWeight: 700,
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                    }}
                  >
                    <User size={18} color="var(--accent-primary)" />
                    Hablante {h.hablante}
                  </h3>
                  <span
                    className="mono-num"
                    style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}
                  >
                    {h.segundos_habla.toFixed(1)} segundos de habla
                  </span>
                </div>

                {eleccionActual && (
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.25rem",
                      fontSize: "0.75rem",
                      color: "var(--accent-primary)",
                      fontWeight: 700,
                    }}
                  >
                    <CheckCircle2 size={16} /> Confirmado
                  </span>
                )}
              </div>

              {/* Propuesta del modelo (en modo manual llega sin ella) */}
              {h.propuesta ? (
                <div
                  style={{
                    background: esDudosa ? "rgba(245, 158, 11, 0.1)" : "var(--bg-surface-elevated)",
                    border: `1px solid ${esDudosa ? "rgba(245, 158, 11, 0.35)" : "var(--border-subtle)"}`,
                    borderRadius: "var(--radius-md)",
                    padding: "0.75rem 1rem",
                    marginBottom: "1rem",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: "0.25rem",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "0.75rem",
                        color: "var(--text-muted)",
                        textTransform: "uppercase",
                        fontWeight: 600,
                      }}
                    >
                      Propuesta del modelo
                    </span>
                    <span
                      className="mono-num"
                      style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}
                    >
                      Confianza: {(h.propuesta.confianza * 100).toFixed(0)}%
                    </span>
                  </div>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <span
                      style={{ fontSize: "0.95rem", fontWeight: 700, textTransform: "capitalize" }}
                    >
                      Voz {h.propuesta.etiqueta}
                    </span>

                    {esDudosa && (
                      <span
                        style={{
                          fontSize: "0.7rem",
                          fontWeight: 700,
                          padding: "0.15rem 0.5rem",
                          borderRadius: "var(--radius-full)",
                          background: "rgba(245, 158, 11, 0.2)",
                          color: "var(--voz-indeterminado)",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.25rem",
                        }}
                      >
                        <AlertTriangle size={12} /> Propuesta dudosa (RF-06)
                      </span>
                    )}
                  </div>
                </div>
              ) : (
                <div
                  style={{
                    background: "rgba(255,255,255,0.02)",
                    borderRadius: "var(--radius-md)",
                    padding: "0.6rem 0.85rem",
                    marginBottom: "1rem",
                    fontSize: "0.8rem",
                    color: "var(--text-muted)",
                  }}
                >
                  Modo manual: decide exclusivamente escuchando las muestras de voz sin sugerencia
                  previa.
                </div>
              )}

              {/* Fragmentos para escuchar (al menos 3, RF-07) */}
              <div style={{ marginBottom: "1.25rem" }}>
                <span
                  style={{
                    fontSize: "0.8rem",
                    color: "var(--text-secondary)",
                    fontWeight: 600,
                    display: "block",
                    marginBottom: "0.5rem",
                  }}
                >
                  Fragmentos de audio ({h.fragmentos.length} muestras):
                </span>
                <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                  {h.fragmentos.map((f, idx) => {
                    const dur = (f.fin - f.inicio).toFixed(1);
                    return (
                      <button
                        key={`${f.inicio}-${idx}`}
                        onClick={() =>
                          onPlayAudio(
                            f.inicio,
                            f.fin,
                            h.hablante,
                            `Hablante ${h.hablante} · Muestra ${idx + 1} (${dur}s)`,
                          )
                        }
                        className="btn btn-secondary btn-sm"
                        style={{ display: "inline-flex", gap: "0.35rem" }}
                        title={`Escuchar fragmento ${idx + 1}`}
                      >
                        <Play size={12} />
                        Muestra {idx + 1} ({dur}s)
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Opciones de confirmación: Femenino, Masculino, Indeterminado (Regla 8) */}
              <div>
                <span
                  style={{
                    fontSize: "0.8rem",
                    color: "var(--text-secondary)",
                    fontWeight: 600,
                    display: "block",
                    marginBottom: "0.5rem",
                  }}
                >
                  Confirmar etiqueta:
                </span>
                <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "0.45rem" }}>
                  <button
                    onClick={() => seleccionarEtiqueta(h.hablante, "femenino")}
                    style={{
                      padding: "0.6rem 0.85rem",
                      borderRadius: "var(--radius-md)",
                      border:
                        eleccionActual === "femenino"
                          ? "2px solid #10b981"
                          : "1px solid var(--border-subtle)",
                      background:
                        eleccionActual === "femenino"
                          ? "var(--voz-femenina-bg)"
                          : "var(--bg-surface-elevated)",
                      color: eleccionActual === "femenino" ? "#10b981" : "var(--text-primary)",
                      fontWeight: 600,
                      fontSize: "0.85rem",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    <span>Voz percibida femenina</span>
                    {eleccionActual === "femenino" && <Check size={16} />}
                  </button>

                  <button
                    onClick={() => seleccionarEtiqueta(h.hablante, "masculino")}
                    style={{
                      padding: "0.6rem 0.85rem",
                      borderRadius: "var(--radius-md)",
                      border:
                        eleccionActual === "masculino"
                          ? "2px solid #818cf8"
                          : "1px solid var(--border-subtle)",
                      background:
                        eleccionActual === "masculino"
                          ? "var(--voz-masculina-bg)"
                          : "var(--bg-surface-elevated)",
                      color: eleccionActual === "masculino" ? "#818cf8" : "var(--text-primary)",
                      fontWeight: 600,
                      fontSize: "0.85rem",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    <span>Voz percibida masculina</span>
                    {eleccionActual === "masculino" && <Check size={16} />}
                  </button>

                  <button
                    onClick={() => seleccionarEtiqueta(h.hablante, "indeterminado")}
                    style={{
                      padding: "0.6rem 0.85rem",
                      borderRadius: "var(--radius-md)",
                      border:
                        eleccionActual === "indeterminado"
                          ? "2px solid #f59e0b"
                          : "1px solid var(--border-subtle)",
                      background:
                        eleccionActual === "indeterminado"
                          ? "var(--voz-indeterminado-bg)"
                          : "var(--bg-surface-elevated)",
                      color: eleccionActual === "indeterminado" ? "#f59e0b" : "var(--text-primary)",
                      fontWeight: 600,
                      fontSize: "0.85rem",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    <span>Indeterminado (RN-03)</span>
                    {eleccionActual === "indeterminado" && <Check size={16} />}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Bloque de validación y botón de confirmar */}
      <div
        className="card"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1.25rem",
          background: "var(--bg-surface-elevated)",
        }}
      >
        <div>
          <div style={{ fontWeight: 700, fontSize: "1rem" }}>
            {todosConfirmados
              ? "Todas las voces presentes han sido confirmadas"
              : `Faltan ${faltanPorConfirmar.length} voces por confirmar`}
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            {todosConfirmados
              ? "Se guardará el registro de supervisión humana y se procederá al cálculo de métricas (Fase 2)."
              : "Requisito estricto (RN-01): es necesario asignar una opción a cada hablante presente antes de ver resultados."}
          </div>
        </div>

        <button
          onClick={handleConfirmar}
          disabled={!todosConfirmados || enviando}
          className="btn btn-primary"
          style={{ padding: "0.85rem 1.85rem", fontSize: "1rem" }}
        >
          {enviando ? "Analizando episodio..." : "Confirmar y ver resultados"}
          <ArrowRight size={18} />
        </button>
      </div>

      {errorEnvio && (
        <div
          style={{ marginTop: "1rem", color: "#ef4444", fontSize: "0.85rem", textAlign: "right" }}
        >
          {errorEnvio}
        </div>
      )}
    </div>
  );
};
