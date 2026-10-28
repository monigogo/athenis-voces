/**
 * Pruebas del cliente de la API (9.3; specs/003-producto/contracts/api-http.md).
 *
 * Con el backend conectado, la web usa sus rutas: nada se inventa. Sin backend, sigue el modo demo.
 * fetch es falso: cada prueba dice qué responde cada ruta.
 */

import { afterEach, describe, expect, it, vi } from "vitest";
import { EJEMPLO_CON_VOCES_FEMENINAS } from "../data/ejemplos";
import { ApiClient, tramoDeEvento, tramoDeVoz, urlFragmento } from "../services/api";
import { audioService } from "../services/audioPlayer";
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

  it("subir un audio en modo manual lo pide al backend (RF-08)", async () => {
    const { api, fetch } = await conectada({
      "POST /api/analisis": () => json(estado("a1", "en_cola"), 201),
      "GET /api/analisis/a1": () => json(estado("a1", "esperando_confirmacion")),
    });

    await api.subirAudio(audio(), () => {}, true);

    const cuerpo = llamada(fetch, "POST", "/api/analisis").body as FormData;
    expect(cuerpo.get("modo_manual")).toBe("true");
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

  it("en modo manual las voces llegan sin propuesta", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("sin conexión");
      }),
    );
    const api = new ApiClient({ intervaloMs: 0 });
    await api.checkSalud();

    try {
      const subida = api.subirAudio(audio(), () => {}, true);
      await vi.runAllTimersAsync();
      const { id_analisis } = await subida;

      const { hablantes } = await api.getHablantes(id_analisis);
      expect(hablantes.length).toBeGreaterThan(0);
      expect(hablantes.every((h) => h.propuesta === null)).toBe(true);
    } finally {
      vi.useRealTimers();
    }
  });
});

describe("fragmentos de audio (RF-18)", () => {
  it("una interrupción empieza 1 s antes y acaba después", () => {
    expect(tramoDeEvento(30, 32, 120)).toEqual({ inicio: 29, fin: 32.5 });
  });

  it("una interrupción larga se corta a 15 s", () => {
    expect(tramoDeEvento(30, 60, 120)).toEqual({ inicio: 29, fin: 44 });
  });

  it("una interrupción al principio del audio no empieza antes de 0", () => {
    expect(tramoDeEvento(0.4, 2, 120)).toEqual({ inicio: 0, fin: 2.5 });
  });

  it("una interrupción al final del audio no pasa de su duración", () => {
    expect(tramoDeEvento(118, 119.8, 120)).toEqual({ inicio: 117, fin: 120 });
  });

  it("una muestra de voz suena tal cual", () => {
    expect(tramoDeVoz(1, 4)).toEqual({ inicio: 1, fin: 4 });
  });

  it("una muestra de voz larga se corta a 15 s", () => {
    expect(tramoDeVoz(10, 40)).toEqual({ inicio: 10, fin: 25 });
  });

  it("un turno no pasa de la duración del audio", () => {
    expect(tramoDeVoz(110, 124, 120)).toEqual({ inicio: 110, fin: 120 });
  });

  it("la URL pide el tramo a la ruta del fragmento", () => {
    expect(urlFragmento("a1", { inicio: 29, fin: 32.5 })).toBe(
      "/api/analisis/a1/fragmento?inicio=29&fin=32.5",
    );
  });

  it("con backend y un audio subido, el fragmento se pide al backend", async () => {
    const { api } = await conectada({
      "POST /api/analisis": () => json(estado("a1", "en_cola"), 201),
      "GET /api/analisis/a1": () => json(estado("a1", "esperando_confirmacion")),
    });

    await api.subirAudio(audio(), () => {});

    expect(api.hayAudio()).toBe(true);
    expect(api.urlFragmentoActual({ inicio: 29, fin: 32.5 })).toBe(
      "/api/analisis/a1/fragmento?inicio=29&fin=32.5",
    );
  });

  it("un ejemplo precalculado no tiene audio", async () => {
    const { api } = await conectada({
      "POST /api/analisis": () => json(estado("e1", "terminado"), 201),
      "GET /api/analisis/e1/resultado": () =>
        json({ ...EJEMPLO_CON_VOCES_FEMENINAS, id_analisis: "e1" }),
    });

    await api.iniciarEjemplo("ejemplo-con-voces-femeninas");

    expect(api.hayAudio()).toBe(false);
    expect(api.urlFragmentoActual({ inicio: 29, fin: 32.5 })).toBeNull();
  });
});

describe("audio subido en el navegador", () => {
  it("con backend no se decodifica en el navegador: lo procesa el servidor", async () => {
    const { api } = await conectada({
      "POST /api/analisis": () => json(estado("a1", "en_cola"), 201),
      "GET /api/analisis/a1": () => json(estado("a1", "esperando_confirmacion")),
    });
    vi.mocked(audioService.loadUserAudio).mockClear();

    await api.subirAudio(audio(), () => {});

    expect(audioService.loadUserAudio).not.toHaveBeenCalled();
  });

  it("sin backend se decodifica en el navegador para el modo demo", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("sin conexión");
      }),
    );
    const api = new ApiClient({ intervaloMs: 0 });
    await api.checkSalud();
    vi.mocked(audioService.loadUserAudio).mockClear();

    try {
      const subida = api.subirAudio(audio(), () => {});
      await vi.runAllTimersAsync();
      await subida;

      expect(audioService.loadUserAudio).toHaveBeenCalledTimes(1);
    } finally {
      vi.useRealTimers();
    }
  });
});
