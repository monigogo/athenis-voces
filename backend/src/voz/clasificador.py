"""Propuesta de la voz de cada hablante mediante inaSpeechSegmenter (RF-06, RN-03).

Import de inaSpeechSegmenter diferido dentro de _cargar_segmenter() para que
pytest -m "not slow" y la CI funcionen sin TensorFlow instalado.
"""

from pathlib import Path

from config import CONFIG
from contrato import EtiquetaVoz, PropuestaVoz, Turno


def _cargar_segmenter():
    """Carga el modelo; import diferido para no requerir TensorFlow en la CI."""
    try:
        from inaSpeechSegmenter import Segmenter
    except (ImportError, ModuleNotFoundError) as exc:
        raise RuntimeError(
            "inaSpeechSegmenter no está instalado. Ejecuta: uv sync --group audio"
        ) from exc
    try:
        return Segmenter()
    except Exception as exc:
        raise RuntimeError(f"No se pudo cargar el modelo de clasificación de voz: {exc}") from exc


def _solo_intervals(hablante: int, all_turnos: list[Turno]) -> list[tuple[float, float]]:
    """Intervalos en los que el hablante habla sin que ningún otro hablante hable a la vez."""
    own = [(t.inicio, t.fin) for t in all_turnos if t.hablante == hablante]
    others = [(t.inicio, t.fin) for t in all_turnos if t.hablante != hablante]
    result: list[tuple[float, float]] = []
    for s, e in own:
        segs = [(s, e)]
        for o_s, o_e in others:
            new_segs: list[tuple[float, float]] = []
            for seg_s, seg_e in segs:
                if o_e <= seg_s or o_s >= seg_e:
                    new_segs.append((seg_s, seg_e))
                else:
                    if o_s > seg_s:
                        new_segs.append((seg_s, o_s))
                    if o_e < seg_e:
                        new_segs.append((o_e, seg_e))
            segs = new_segs
        result.extend(segs)
    return result


def _interseccion(intervals: list[tuple[float, float]], start: float, stop: float) -> float:
    """Segundos del intervalo [start, stop] cubiertos por alguno de los intervals."""
    total = 0.0
    for s, e in intervals:
        total += max(0.0, min(stop, e) - max(start, s))
    return total


def _clasificar(p_female: float) -> tuple[EtiquetaVoz, float]:
    """Etiqueta y confianza en esa etiqueta a partir de la proporción de tiempo femenino."""
    z_min = CONFIG.zona_dudosa_min
    z_max = CONFIG.zona_dudosa_max
    if z_min <= p_female <= z_max:
        return EtiquetaVoz.INDETERMINADO, max(p_female, 1.0 - p_female)
    if p_female > z_max:
        return EtiquetaVoz.FEMENINO, p_female
    return EtiquetaVoz.MASCULINO, 1.0 - p_female


def proponer_voz(wav: Path, turnos: list[Turno]) -> dict[int, PropuestaVoz]:
    """Propone la voz de cada hablante (RF-06).

    Llama a Segmenter una sola vez sobre el WAV completo y distribuye cada
    segmento al hablante por solapamiento de tiempo, descontando los tramos
    compartidos con otros hablantes.
    """
    segmenter = _cargar_segmenter()
    try:
        segmentos: list[tuple[str, float, float]] = segmenter(str(wav))
    except Exception as exc:
        raise RuntimeError(f"El modelo de voz no pudo procesar el audio: {exc}") from exc

    hablantes = sorted({t.hablante for t in turnos})
    resultado: dict[int, PropuestaVoz] = {}
    for hablante in hablantes:
        solo = _solo_intervals(hablante, turnos)
        t_female = 0.0
        t_male = 0.0
        for label, start, stop in segmentos:
            if label == "female":
                t_female += _interseccion(solo, start, stop)
            elif label == "male":
                t_male += _interseccion(solo, start, stop)

        total = t_female + t_male
        if total == 0.0:
            etiqueta, confianza = EtiquetaVoz.INDETERMINADO, 0.5
        else:
            etiqueta, confianza = _clasificar(t_female / total)

        resultado[hablante] = PropuestaVoz(etiqueta=etiqueta, confianza=confianza)
    return resultado
