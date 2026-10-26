import { BookOpen, CheckCircle2, FileAudio, Radio, SlidersHorizontal } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { AudioPlayerBar } from "./components/AudioPlayerBar";
import { api } from "./services/api";
import type { Resultado } from "./types/contrato";
import { AnalizarView } from "./views/AnalizarView";
import { ComoFuncionaView } from "./views/ComoFuncionaView";
import { ConfirmarVocesView } from "./views/ConfirmarVocesView";
import { ResultadosView } from "./views/ResultadosView";

type Tab = "analizar" | "confirmar" | "resultados" | "como-funciona";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>("analizar");
  const [currentAnalisisId, setCurrentAnalisisId] = useState<string | null>(null);
  const [resultadoActual, setResultadoActual] = useState<Resultado | null>(null);
  const [backendConectado, setBackendConectado] = useState(false);
  const [currentTrack, setCurrentTrack] = useState<{
    titulo: string;
    inicio: number;
    fin: number;
    hablante?: number;
  } | null>(null);

  // Comprobar salud del backend
  useEffect(() => {
    api.checkSalud().then((conectado) => {
      setBackendConectado(conectado);
    });
  }, []);

  const handleAnalisisIniciado = (id: string) => {
    setCurrentAnalisisId(id);
    setActiveTab("confirmar");
  };

  const handleEjemploSeleccionado = (res: Resultado) => {
    setCurrentAnalisisId(res.id_analisis);
    setResultadoActual(res);
    setActiveTab("resultados");
  };

  const handleConfirmacionCompleta = (res: Resultado) => {
    setResultadoActual(res);
    setActiveTab("resultados");
  };

  const handlePlayAudio = (
    inicio: number,
    fin: number,
    hablante = 1,
    titulo = "Fragmento de audio",
  ) => {
    setCurrentTrack({
      titulo,
      inicio,
      fin,
      hablante,
    });
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Barra de navegación superior */}
      <header className="header-nav">
        <div className="brand-container">
          <div className="brand-logo-icon">
            <Radio size={20} />
          </div>
          <div>
            <div className="brand-title">
              <span>Athenis Voces</span>
              <span className="brand-tag">v0.2</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
              Análisis ético de voz y turnos de conversación
            </div>
          </div>
        </div>

        {/* Pestañas de las 4 pantallas del flujo (8.2) */}
        <nav className="nav-tabs" aria-label="Navegación principal">
          <button
            onClick={() => setActiveTab("analizar")}
            className={`nav-tab-button ${activeTab === "analizar" ? "active" : ""}`}
            id="tab-analizar"
          >
            <FileAudio size={16} />
            1. Analizar
          </button>

          <button
            onClick={() => setActiveTab("confirmar")}
            disabled={!currentAnalisisId && !resultadoActual}
            className={`nav-tab-button ${activeTab === "confirmar" ? "active" : ""}`}
            id="tab-confirmar"
            title={!currentAnalisisId ? "Inicia un análisis para confirmar voces" : ""}
          >
            <CheckCircle2 size={16} />
            2. Confirmar voces
          </button>

          <button
            onClick={() => setActiveTab("resultados")}
            disabled={!resultadoActual}
            className={`nav-tab-button ${activeTab === "resultados" ? "active" : ""}`}
            id="tab-resultados"
            title={!resultadoActual ? "Completa la confirmación para ver resultados" : ""}
          >
            <SlidersHorizontal size={16} />
            3. Resultados
          </button>

          <button
            onClick={() => setActiveTab("como-funciona")}
            className={`nav-tab-button ${activeTab === "como-funciona" ? "active" : ""}`}
            id="tab-como-funciona"
          >
            <BookOpen size={16} />
            Cómo funciona
          </button>
        </nav>

        {/* Estado de conexión */}
        <div className="header-actions">
          <div
            className="status-badge"
            title={backendConectado ? "Backend FastAPI conectado" : "Modo demostración integrado"}
          >
            <span className={`status-dot ${backendConectado ? "pulsing" : ""}`} />
            <span>{backendConectado ? "Backend API" : "Modo Local / Demo"}</span>
          </div>
        </div>
      </header>

      {/* Contenido principal */}
      <main
        className="main-content"
        style={{ flex: 1, paddingBottom: currentTrack ? "6rem" : "3rem" }}
      >
        {activeTab === "analizar" && (
          <AnalizarView
            onAnalisisIniciado={handleAnalisisIniciado}
            onEjemploSeleccionado={handleEjemploSeleccionado}
          />
        )}

        {activeTab === "confirmar" && currentAnalisisId && (
          <ConfirmarVocesView
            idAnalisis={currentAnalisisId}
            onConfirmacionCompleta={handleConfirmacionCompleta}
            onPlayAudio={handlePlayAudio}
          />
        )}

        {activeTab === "resultados" && resultadoActual && (
          <ResultadosView
            resultado={resultadoActual}
            onNuevoAnalisis={() => setActiveTab("analizar")}
            onPlayAudio={handlePlayAudio}
          />
        )}

        {activeTab === "como-funciona" && <ComoFuncionaView />}
      </main>

      {/* Reproductor de audio fijo inferior */}
      <AudioPlayerBar currentTrack={currentTrack} onClose={() => setCurrentTrack(null)} />

      {/* Pie de página ético */}
      <footer
        style={{
          borderTop: "1px solid var(--border-subtle)",
          padding: "1.5rem",
          textAlign: "center",
          fontSize: "0.8rem",
          color: "var(--text-muted)",
          background: "var(--bg-surface)",
        }}
      >
        <p>
          Athenis Voces · Desarrollado para el reto Women in Open AI · Código abierto bajo
          Constitución ética · Datos eliminados tras 24 h.
        </p>
      </footer>
    </div>
  );
};
