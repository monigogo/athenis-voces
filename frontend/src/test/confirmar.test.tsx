/**
 * Pruebas del modo manual y de la confirmación de voces (RF-08, RN-02, regla 8).
 *
 * El modo manual se elige antes de subir el audio. Ninguna voz sale confirmada sin que la persona
 * la confirme.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { EJEMPLO_CON_VOCES_FEMENINAS } from "../data/ejemplos";
import { api } from "../services/api";
import type { HablantesParaConfirmar } from "../types/contrato";
import { AnalizarView } from "../views/AnalizarView";
import { ConfirmarVocesView } from "../views/ConfirmarVocesView";

const fragmentos = [
  { inicio: 1, fin: 4 },
  { inicio: 10, fin: 13 },
  { inicio: 20, fin: 23 },
];

const hablantes: HablantesParaConfirmar = {
  version_contrato: "0.2",
  id_analisis: "a1",
  hablantes: [
    {
      hablante: 1,
      segundos_habla: 30,
      propuesta: { etiqueta: "femenino", confianza: 0.9 },
      fragmentos,
    },
    {
      hablante: 2,
      segundos_habla: 25,
      propuesta: { etiqueta: "masculino", confianza: 0.9 },
      fragmentos,
    },
  ],
};

function confirmar() {
  return render(
    <ConfirmarVocesView idAnalisis="a1" onConfirmacionCompleta={() => {}} onPlayAudio={() => {}} />,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("confirmar voces", () => {
  it("ninguna voz sale confirmada sin que la persona la confirme", async () => {
    vi.spyOn(api, "getHablantes").mockResolvedValue(hablantes);

    confirmar();

    expect(await screen.findByText("Hablante 1")).toBeInTheDocument();
    expect(screen.queryByText("Confirmado")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Confirmar y ver resultados/ })).toBeDisabled();
  });

  it("envía lo que elige la persona y si coincide con la propuesta", async () => {
    vi.spyOn(api, "getHablantes").mockResolvedValue(hablantes);
    const enviar = vi
      .spyOn(api, "enviarConfirmacion")
      .mockResolvedValue({ ...EJEMPLO_CON_VOCES_FEMENINAS, id_analisis: "a1" });

    confirmar();
    await screen.findByText("Hablante 1");
    const [femenina1] = screen.getAllByRole("button", { name: /Voz percibida femenina/ });
    const [, indeterminado2] = screen.getAllByRole("button", { name: /Indeterminado/ });
    fireEvent.click(femenina1);
    fireEvent.click(indeterminado2);
    fireEvent.click(screen.getByRole("button", { name: /Confirmar y ver resultados/ }));

    await waitFor(() => expect(enviar).toHaveBeenCalled());
    expect(enviar).toHaveBeenCalledWith("a1", {
      version_contrato: "0.2",
      etiquetas: [
        { hablante: 1, etiqueta: "femenino", origen: "modelo" },
        { hablante: 2, etiqueta: "indeterminado", origen: "persona" },
      ],
    });
  });

  it("la pantalla de confirmar ya no cambia el modo manual", async () => {
    vi.spyOn(api, "getHablantes").mockResolvedValue(hablantes);

    confirmar();

    await screen.findByText("Hablante 1");
    expect(screen.queryByRole("button", { name: /modo manual/i })).not.toBeInTheDocument();
  });
});

describe("analizar", () => {
  it("el modo manual se elige antes de subir y llega a la subida", async () => {
    const subir = vi.spyOn(api, "subirAudio").mockResolvedValue({ id_analisis: "a1" });
    const { container } = render(
      <AnalizarView onAnalisisIniciado={() => {}} onEjemploSeleccionado={() => {}} />,
    );

    fireEvent.click(screen.getByRole("checkbox", { name: /modo manual/i }));
    const entrada = container.querySelector('input[type="file"]') as HTMLInputElement;
    const archivo = new File([new Uint8Array([1])], "reunion.wav", { type: "audio/wav" });
    fireEvent.change(entrada, { target: { files: [archivo] } });

    await waitFor(() => expect(subir).toHaveBeenCalled());
    expect(subir).toHaveBeenCalledWith(archivo, expect.any(Function), true);
  });
});
