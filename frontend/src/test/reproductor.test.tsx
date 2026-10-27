/**
 * Pruebas del reproductor de fragmentos (RF-18; specs/003-producto/contracts/api-http.md).
 *
 * Con un audio subido suena el WAV que da el backend. Un ejemplo precalculado no tiene audio.
 */

import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AudioPlayerBar } from "../components/AudioPlayerBar";
import { api } from "../services/api";
import { audioService } from "../services/audioPlayer";

const pista = { titulo: "Interrupción", inicio: 29, fin: 32.5, hablante: 2 };

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("barra del reproductor", () => {
  it("con un audio subido reproduce el fragmento del backend", () => {
    vi.spyOn(api, "hayAudio").mockReturnValue(true);
    vi.spyOn(api, "urlFragmentoActual").mockReturnValue(
      "/api/analisis/a1/fragmento?inicio=29&fin=32.5",
    );
    const reproducir = vi.spyOn(audioService, "playSegment").mockResolvedValue();
    vi.spyOn(audioService, "stop").mockImplementation(() => {});

    render(<AudioPlayerBar currentTrack={pista} />);

    expect(reproducir).toHaveBeenCalledWith(
      29,
      32.5,
      expect.any(Function),
      "/api/analisis/a1/fragmento?inicio=29&fin=32.5",
    );
  });

  it("con un ejemplo no suena nada y lo dice", () => {
    vi.spyOn(api, "hayAudio").mockReturnValue(false);
    const reproducir = vi.spyOn(audioService, "playSegment").mockResolvedValue();
    vi.spyOn(audioService, "stop").mockImplementation(() => {});

    render(<AudioPlayerBar currentTrack={pista} />);

    expect(reproducir).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: /reanudar reproducción/i })).toBeDisabled();
    expect(screen.getByText("Ejemplo sintético, sin audio")).toBeInTheDocument();
  });
});

describe("fragmento del backend", () => {
  it.each([409, 410, 422])("si responde %i, se muestra su motivo", async (status) => {
    const motivo = `Motivo del servidor (${status})`;
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify({ detail: motivo }), { status })),
    );

    await expect(
      audioService.playSegment(29, 32.5, () => {}, "/api/analisis/a1/fragmento?inicio=29&fin=32.5"),
    ).rejects.toThrow(motivo);
  });
});
