"""Ayudas comunes de las pruebas del análisis: los 3 ejemplos de resultado como casos de prueba."""

from pathlib import Path

import contrato as c

CARPETA = Path(__file__).parent / "ejemplos"
ESCENARIOS = ["con_voces_femeninas", "sin_voces_femeninas", "muchas_interrupciones"]


def cargar_ejemplo(nombre):
    return c.Resultado.model_validate_json((CARPETA / f"{nombre}.json").read_text(encoding="utf-8"))


def entrada_de(resultado):
    """La entrada del análisis que daría el resultado de ejemplo: sus turnos y sus etiquetas."""
    return c.EntradaAnalisis(
        duracion=resultado.duracion,
        turnos=resultado.turnos,
        solapamientos=resultado.solapamientos,
        etiquetas=[
            c.EtiquetaConfirmada(hablante=h.hablante, etiqueta=h.etiqueta, origen=h.origen)
            for h in resultado.hablantes
        ],
    )


def senales_de(resultado):
    return [i for i in resultado.interrupciones if not i.tipo.cuenta_como_interrupcion]


def turno(hablante, inicio, fin):
    return c.Turno(hablante=hablante, inicio=inicio, fin=fin)


def entrada(turnos, etiquetas, duracion=200.0):
    """Entrada a mano. etiquetas = {hablante: etiqueta}; los demás hablantes son voces cortas."""
    return c.EntradaAnalisis(
        duracion=duracion,
        turnos=turnos,
        solapamientos=[],
        etiquetas=[
            c.EtiquetaConfirmada(hablante=h, etiqueta=e, origen="persona")
            for h, e in etiquetas.items()
        ],
    )


def senal(interrumpe, interrumpido, inicio, fin):
    return c.Interrupcion(
        interrumpe=interrumpe,
        interrumpido=interrumpido,
        tipo=c.TipoSolapamiento.SENAL_DE_ESCUCHA,
        inicio=inicio,
        fin=fin,
    )
