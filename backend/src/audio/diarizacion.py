"""Diarización de audio con pyannote (RF-05).

Separa las voces de un WAV mono 16 kHz y devuelve los turnos de cada hablante
y todos los solapamientos detectados, sin filtrar por duración.

Restricciones:
- El import de pyannote.audio está dentro de _cargar_pipeline(), no al inicio
  del módulo, para no requerir el grupo «audio» en la CI rápida.
- HF_TOKEN se lee del entorno; nunca se registra en logs ni en mensajes de error.
- Usa la GPU si la hay y, si no, la CPU (FR-011, SC-007). La variable de entorno
  DISPOSITIVO (auto, cpu o cuda) lo fuerza; por defecto, auto.
- No devuelve ni almacena embeddings ni huellas de voz (RD-04).
- Con cero o un hablante devuelve los turnos detectados sin lanzar excepción;
  el error por pocas voces lo gestiona el pipeline (D-17, voces_presentes_minimas).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from contrato import Solapamiento, Turno

# ---------------------------------------------------------------------------
# Dispositivo: GPU o CPU
# ---------------------------------------------------------------------------

DISPOSITIVOS = ("auto", "cpu", "cuda")


def elegir_dispositivo(valor: str | None, hay_gpu: bool) -> str:
    """«cuda» o «cpu» según DISPOSITIVO; con «auto» (o sin valor), la GPU si la hay.

    Pedir «cuda» sin GPU es un error: pasar a la CPU en silencio haría medir otra cosa (RNF-01).
    """
    pedido = (valor or "auto").strip().lower()
    if pedido not in DISPOSITIVOS:
        raise ValueError(f"DISPOSITIVO={valor!r} no es válido; usa auto, cpu o cuda")
    if pedido == "auto":
        return "cuda" if hay_gpu else "cpu"
    if pedido == "cuda" and not hay_gpu:
        raise RuntimeError("DISPOSITIVO=cuda, pero no hay GPU disponible; usa auto o cpu")
    return pedido


# ---------------------------------------------------------------------------
# Carga del modelo (aislada para facilitar el mock en tests)
# ---------------------------------------------------------------------------


def _cargar_pipeline() -> Any:
    """Carga Pipeline de pyannote y la lleva a la GPU o a la CPU (elegir_dispositivo).

    Separada de diarizar() para que los tests puedan parchearla directamente.
    Lanza excepción descriptiva si el modelo no está disponible o falta HF_TOKEN,
    sin incluir el valor del token en el mensaje.
    """
    try:
        from pyannote.audio import Pipeline  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "pyannote.audio no está instalado. Ejecuta: uv sync --group audio"
        ) from exc

    import torch  # type: ignore[import-untyped]

    # Antes de descargar el modelo, para que un DISPOSITIVO mal escrito falle al momento
    dispositivo = elegir_dispositivo(os.environ.get("DISPOSITIVO"), torch.cuda.is_available())

    token = os.environ.get("HF_TOKEN")
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-community-1",
            token=token,  # pyannote 4 ya no acepta use_auth_token
        )
    except Exception as exc:
        # No incluimos el valor del token en el mensaje (RD-04)
        token_info = "HF_TOKEN presente" if token else "HF_TOKEN ausente"
        raise RuntimeError(
            f"No se pudo cargar el modelo de diarización ({token_info}). "
            f"Motivo técnico: {type(exc).__name__}"
        ) from exc

    pipeline.to(torch.device(dispositivo))
    return pipeline


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------


def diarizar(wav: Path) -> tuple[list[Turno], list[Solapamiento]]:
    """Separa hablantes en *wav* y devuelve turnos y solapamientos.

    Los hablantes se numeran 1, 2, 3… por orden de primera aparición y de forma
    estable para el mismo audio.  Los tramos de duración cero se descartan.
    Todos los solapamientos detectados se incluyen, sin filtrar por duración.

    No lanza excepción por número de hablantes; esa validación corresponde al
    pipeline (D-17, voces_presentes_minimas).
    """
    pipeline = _cargar_pipeline()
    salida = pipeline(str(wav))
    # community-1 devuelve un DiarizeOutput con la anotación dentro; otros pipelines, la anotación
    anotacion = getattr(salida, "speaker_diarization", salida)

    # -----------------------------------------------------------------------
    # Construir segmentos brutos: (inicio, fin, etiqueta_pyannote)
    # -----------------------------------------------------------------------
    segmentos: list[tuple[float, float, str]] = []
    for segmento, _track, etiqueta in anotacion.itertracks(yield_label=True):
        inicio = float(segmento.start)
        fin = float(segmento.end)
        if fin <= inicio:  # descarta tramos de duración cero o negativos
            continue
        segmentos.append((inicio, fin, etiqueta))

    # -----------------------------------------------------------------------
    # Asignar número de hablante por orden de primera aparición (estable)
    # -----------------------------------------------------------------------
    orden_aparicion: dict[str, int] = {}
    for inicio, _fin, etiqueta in sorted(segmentos, key=lambda s: s[0]):
        if etiqueta not in orden_aparicion:
            orden_aparicion[etiqueta] = len(orden_aparicion) + 1

    # -----------------------------------------------------------------------
    # Construir turnos
    # -----------------------------------------------------------------------
    turnos: list[Turno] = [
        Turno(inicio=inicio, fin=fin, hablante=orden_aparicion[etiq])
        for inicio, fin, etiq in segmentos
    ]

    # -----------------------------------------------------------------------
    # Detectar solapamientos: tramos donde se pisan ≥ 2 hablantes
    # -----------------------------------------------------------------------
    solapamientos = _detectar_solapamientos(segmentos, orden_aparicion)

    return turnos, solapamientos


# ---------------------------------------------------------------------------
# Detección de solapamientos
# ---------------------------------------------------------------------------


def _detectar_solapamientos(
    segmentos: list[tuple[float, float, str]],
    orden_aparicion: dict[str, int],
) -> list[Solapamiento]:
    """Detecta todos los intervalos donde dos o más hablantes hablan a la vez.

    Algoritmo de barrido de eventos:
    - Para cada inicio/fin de segmento se genera un evento.
    - Se recorren en orden cronológico manteniendo el conjunto de hablantes activos.
    - Cuando hay ≥ 2 activos, el intervalo [evento_actual, evento_siguiente] es
      un solapamiento (si tiene duración > 0).
    """
    if len(segmentos) < 2:
        return []

    # Eventos: (tiempo, tipo, numero_hablante)  tipo: +1 = inicio, -1 = fin
    eventos: list[tuple[float, int, int]] = []
    for inicio, fin, etiq in segmentos:
        num = orden_aparicion[etiq]
        eventos.append((inicio, +1, num))
        eventos.append((fin, -1, num))

    # Ordenar: mismo tiempo → primero los finales (evita solapamientos de duración 0)
    eventos.sort(key=lambda e: (e[0], e[1]))

    activos: set[int] = set()
    solapamientos: list[Solapamiento] = []
    t_anterior = 0.0

    for tiempo, tipo, num in eventos:
        if len(activos) >= 2 and tiempo > t_anterior:
            solapamientos.append(
                Solapamiento(
                    inicio=t_anterior,
                    fin=tiempo,
                    hablantes=sorted(activos),
                )
            )
        t_anterior = tiempo
        if tipo == +1:
            activos.add(num)
        else:
            activos.discard(num)

    return solapamientos
