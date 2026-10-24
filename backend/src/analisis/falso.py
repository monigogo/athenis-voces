"""Falso del análisis (plan, B05): devuelve un resultado de ejemplo en vez de calcularlo.

Sirve para probar el recorrido completo mientras el análisis real no está listo. Los resultados no
dependen de los turnos que llegan: son los tres ejemplos de tests/ejemplos. Se elige uno según las
etiquetas confirmadas, o por nombre con escenario=.
"""

from pathlib import Path

from contrato import EntradaAnalisis, EtiquetaVoz, Resultado

EJEMPLOS = Path(__file__).resolve().parents[2] / "tests" / "ejemplos"


def escenarios() -> list[str]:
    """Nombres de los ejemplos disponibles."""
    return sorted(fichero.stem for fichero in EJEMPLOS.glob("*.json"))


def analizar(entrada: EntradaAnalisis, escenario: str | None = None) -> Resultado:
    """Mismo contrato que el análisis real: EntradaAnalisis -> Resultado."""
    if escenario is None:
        hay_femenina = any(e.etiqueta is EtiquetaVoz.FEMENINO for e in entrada.etiquetas)
        escenario = "con_voces_femeninas" if hay_femenina else "sin_voces_femeninas"
    if escenario not in escenarios():
        raise ValueError(
            f"Escenario desconocido «{escenario}». Disponibles: {', '.join(escenarios())}"
        )
    return Resultado.model_validate_json(
        (EJEMPLOS / f"{escenario}.json").read_text(encoding="utf-8")
    )
