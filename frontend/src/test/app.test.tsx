import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "../App";

describe("Aplicación Athenis Voces Frontend", () => {
  it("renderiza la barra de navegación con el título del proyecto", () => {
    render(<App />);
    expect(screen.getByText("Athenis Voces")).toBeInTheDocument();
    expect(screen.getByText("1. Analizar")).toBeInTheDocument();
    expect(screen.getByText("Cómo funciona")).toBeInTheDocument();
  });

  it("muestra el aviso de privacidad obligatorio antes de subir audio (8.4)", () => {
    render(<App />);
    expect(
      screen.getByText(/Analizaremos solo las voces de este audio, no lo que se dice/i),
    ).toBeInTheDocument();
  });

  it("permite seleccionar un ejemplo precalculado y ver resultados directamente", async () => {
    render(<App />);
    const botonVerResultados = screen.getAllByText("Ver resultados")[0];
    fireEvent.click(botonVerResultados);

    // Debe navegar a Resultados y mostrar el aviso ético obligatorio de la sección 8.4
    expect(
      await screen.findByText(/Estos datos describen este episodio, no a las personas/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Resultados del análisis acústico")).toBeInTheDocument();
  });

  it("permite navegar a la página 'Cómo funciona' (RF-22)", () => {
    render(<App />);
    const tabComoFunciona = screen.getByText("Cómo funciona");
    fireEvent.click(tabComoFunciona);

    expect(screen.getByText("Cómo funciona Athenis Voces")).toBeInTheDocument();
    expect(screen.getByText(/Glosario acústico y conversacional/i)).toBeInTheDocument();
  });
});
