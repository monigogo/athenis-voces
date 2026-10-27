/**
 * Pruebas del cliente de la API (9.3; specs/003-producto/contracts/api-http.md).
 *
 * Con el backend conectado, la web usa sus rutas: nada se inventa. Sin backend, sigue el modo demo.
 * fetch es falso: cada prueba dice qué responde cada ruta.
 */

import { afterEach, describe, expect, it, vi } from "vitest";
import { EJEMPLO_CON_VOCES_FEMENINAS } from "../data/ejemplos";
import { ApiClient } from "../services/api";
import type { Confirmacion, Estado, HablantesParaConfirmar } from "../types/contrato";

// El reproductor no es lo que se prueba aquí (y el File de jsdom no tiene arrayBuffer)
vi.mock("../services/audioPlayer", () => ({
  audioService: { stop: vi.fn(), loadUserAudio: vi.fn(async () => {}) },
}));

type Respuesta = () => Response;

function json(cuerpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(cuerpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function estado(id: string, e: Estado, extra: Record<string, unknown> = {}) {
  return {
    version_contrato: "0.2",
    id_analisis: id,
    estado: e,
    progreso: null,
    motivo_error: null,
    ...extra,
  };
}

/** fetch falso. Una lista de respuestas se da en orden: sirve para preguntar el estado varias veces. */
function servidor(rutas: Record<string, Respuesta | Respuesta[]>) {
  const pendientes = Object.fromEntries(
    Object.entries(rutas).map(([clave, r]) => [clave, Array.isArray(r) ? [...r] : r]),
  );
  return vi.fn(async (url: string, init?: RequestInit) => {
    const clave = `${init?.method ?? "GET"} ${url}`;
    const r = pendientes[clave];
    if (!r) throw new Error(`Ruta no esperada: ${clave}`);
    if (Array.isArray(r)) {
      const siguiente = r.length > 1 ? r.shift() : r[0];
      if (!siguiente) throw new Error(`Sin respuesta para ${clave}`);
      return siguiente();
    }
    return r();
  });
}

async function conectada(rutas: Record<string, Respuesta | Respuesta[]>) {
  const fetch = servidor({ "GET /api/salud": () => json({ estado: "ok" }), ...rutas });
  vi.stubGlobal("fetch", fetch);
  const api = new ApiClient({ intervaloMs: 0 });
  expect(await api.checkSalud()).toBe(true);
  return { api, fetch };
}

function llamada(fetch: ReturnType<typeof servidor>, metodo: string, url: string) {
  const encontrada = fetch.mock.calls.find(
    ([u, init]) => u === url && ((init as RequestInit | undefined)?.method ?? "GET") === metodo,
  );
  if (!encontrada) throw new Error(`No se llamó a ${metodo} ${url}`);
  return encontrada[1] as RequestInit;
}

const audio = () => new File([new Uint8Array([1, 2, 3])], "reunion.wav", { type: "audio/wav" });

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("con el backend conectado", () => {
  it("un ejemplo se pide al backend y se muestra su resultado", async () => {
    const { api, fetch } = await conectada({
      "POST /api/analisis": () => json(estado("e1", "terminado"), 201),
      "GET /api/analisis/e1/resultado": () =>
        json({ ...EJEMPLO_CON_VOCES_FEMENINAS, id_analisis: "e1" }),
    });

    const resultado = await api.iniciarEjemplo("ejemplo-con-voces-femeninas");

    expect(resultado.id_analisis).toBe("e1");
    const cuerpo = llamada(fetch, "POST", "/api/analisis").body as FormData;
    expect(cuerpo.get("ejemplo")).toBe("ejemplo-con-voces-femeninas");
  });

  it("subir un audio lo envía y pregunta el estado hasta que espera confirmación", async () => {
    const { api, fetch } = await conectada({
      "POST /api/analisis": () => json(estado("a1", "en_cola"), 201),
      "GET /api/analisis/a1": [
        () => json(estado("a1", "procesando", { progreso: 25 })),
        () => json(estado("a1", "procesando", { progreso: 75 })),
        () => json(estado("a1", "esperando_confirmacion")),
      ],
    });
    const vistos: string[] = [];

    const { id_analisis } = await api.subirAudio(audio(), (e) =>
      vistos.push(`${e.estado}${e.progreso ?? ""}`),
    );

    expect(id_analisis).toBe("a1");
    expect(vistos).toEqual(["en_cola", "procesando25", "procesando75", "esperando_confirmacion"]);
    const cuerpo = llamada(fetch, "POST", "/api/analisis").body as FormData;
    expect((cuerpo.get("audio") as File).name).toBe("reunion.wav");
    expect(cuerpo.get("modo_manual")).toBe("false");
  });

  it("si el análisis acaba en error, se muestra su motivo", async () => {
    const motivo = "Solo se ha detectado una voz que se pueda confirmar; hacen falta al menos 2.";
    const { api } = await conectada({
      "POST /api/analisis": () => json(estado("a1", "en_cola"), 201),
      "GET /api/analisis/a1": () => json(estado("a1", "error", { motivo_error: motivo })),
    });

    await expect(api.subirAudio(audio(), () => {})).rejects.toThrow(motivo);
  });

  it("si el backend rechaza la subida, se muestra su motivo", async () => {
    const { api } = await conectada({
      "POST /api/analisis": () => json({ detail: "El audio supera el tamaño máximo" }, 413),
    });

    await expect(api.subirAudio(audio(), () => {})).rejects.toThrow(
      "El audio supera el tamaño máximo",
    );
  });

  it("los hablantes para confirmar vienen del backend", async () => {
    const hablantes: HablantesParaConfirmar = {
      version_contrato: "0.2",
      id_analisis: "a1",
      hablantes: [
        {
          hablante: 1,
          segundos_habla: 30,
          propuesta: { etiqueta: "indeterminado", confianza: 0.55 },
          fragmentos: [{ inicio: 1, fin: 4 }],
        },
      ],
    };
    const { api } = await conectada({
      "GET /api/analisis/a1/hablantes": () => json(hablantes),
    });

    expect(await api.getHablantes("a1")).toEqual(hablantes);
  });

  it("confirmar envía las etiquetas, espera a que termine y devuelve el resultado", async () => {
    const confirmacion: Confirmacion = {
      version_contrato: "0.2",
      etiquetas: [{ hablante: 1, etiqueta: "femenino", origen: "persona" }],
    };
    const { api, fetch } = await conectada({
      "POST /api/analisis/a1/confirmacion": () =>
        json(estado("a1", "procesando", { progreso: 90 }), 202),
      "GET /api/analisis/a1": [
        () => json(estado("a1", "procesando", { progreso: 90 })),
        () => json(estado("a1", "terminado")),
      ],
      "GET /api/analisis/a1/resultado": () =>
        json({ ...EJEMPLO_CON_VOCES_FEMENINAS, id_analisis: "a1" }),
    });

    const resultado = await api.enviarConfirmacion("a1", confirmacion);

    expect(resultado.id_analisis).toBe("a1");
    const cuerpo = llamada(fetch, "POST", "/api/analisis/a1/confirmacion").body as string;
    expect(JSON.parse(cuerpo)).toEqual(confirmacion);
  });
});

describe("sin backend", () => {
  it("los ejemplos salen de la web, sin pedir nada al backend", async () => {
    const fetch = vi.fn(async () => {
      throw new Error("sin conexión");
    });
    vi.stubGlobal("fetch", fetch);
    const api = new ApiClient({ intervaloMs: 0 });
    expect(await api.checkSalud()).toBe(false);

    const resultado = await api.iniciarEjemplo("ejemplo-con-voces-femeninas");

    expect(resultado.id_analisis).toBe("ejemplo-con-voces-femeninas");
    expect(fetch).toHaveBeenCalledTimes(1); // solo /salud
  });
});
