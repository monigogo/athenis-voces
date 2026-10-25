"""Evaluación (B12): regenera la tabla de la sección 12.1 desde las referencias y las salidas guardadas.

Uso, desde backend/:

    PYTHONPATH=src uv run --group evaluacion python -m evaluacion.evaluar --salidas <carpeta>

- AMI (M-01 a M-04 y la ablación): solo las reuniones de prueba (11.3, RD-05). Por cada una hace
  falta, en la carpeta de salidas, <reunión>.rttm (la separación de voces de pyannote), que basta
  para el DER. M-04 y la ablación necesitan además <reunión>.json (el Resultado del sistema). M-02 y
  M-03 solo usan las voces que etiquetó el modelo en ese .json (las de analizar_audio.py).
- Audios anotados (M-05, su línea base y M-08): en la carpeta de etiquetas, <audio>_referencia.txt
  (el consenso de A y C, guía de anotación 8) y, para la kappa, <audio>_A.txt y <audio>_C.txt. En la
  carpeta de salidas, <audio>.json.
- Tiempo (M-09): los <audio>.tiempo.json de la carpeta de salidas, que guarda analizar_audio.py.

Lo que falta no se evalúa y no cuenta en n. Ninguna salida se usa para ajustar nada (constitución 9).
"""

import argparse
import statistics
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from analisis.analizar import analizar
from config import CONFIG, Config
from contrato import (
    EntradaAnalisis,
    EtiquetaConfirmada,
    EtiquetaVoz,
    OrigenEtiqueta,
    Resultado,
    Turno,
)
from evaluacion import cronometrar, lectura, metricas

REUNIONES_PRUEBA = ("EN2002a", "EN2002c", "ES2004a", "IS1009a", "TS3003a")
RAIZ = Path(__file__).resolve().parents[3]
AMI = RAIZ / "datos" / "ami" / "anotaciones_but" / "only_words" / "rttms" / "test"
ETIQUETAS = RAIZ / "evaluacion" / "etiquetas"
REFERENCIA = "_referencia.txt"
# Audios anotados solo en parte: segundo en que acaba la anotación (guía de anotación, apartado 2).
# Lo que el sistema detecta después no se compara, porque nadie lo ha anotado.
ANOTADO_HASTA = {"EN2002a": 300.0}


@dataclass(frozen=True)
class Reunion:
    nombre: str
    der: metricas.Der  # M-01
    error_femenino: float | None  # M-04, en puntos
    # interrupciones con pyannote frente a con la referencia de AMI
    ablacion: metricas.Deteccion | None
    ideal: bool = False  # True si M-04 y la ablación usan la confirmación ideal (sin .json)
    voces: tuple[metricas.ParVoz, ...] = ()  # M-02 y M-03: (sexo en AMI, propuesta del modelo)


@dataclass(frozen=True)
class Grabacion:
    nombre: str
    sistema: metricas.Deteccion  # M-05
    linea_base: metricas.Deteccion  # cualquier solapamiento (11.3)
    kappa: float | None  # M-08


def entrada_del_resultado(resultado: Resultado) -> EntradaAnalisis:
    """La entrada con la que se calculó un resultado: sus turnos y sus etiquetas confirmadas."""
    return EntradaAnalisis(
        duracion=resultado.duracion,
        turnos=resultado.turnos,
        solapamientos=resultado.solapamientos,
        etiquetas=[
            EtiquetaConfirmada(hablante=h.hablante, etiqueta=h.etiqueta, origen=h.origen)
            for h in resultado.hablantes
        ],
    )


def inicios(resultado: Resultado) -> list[float]:
    """Inicio de cada interrupción que cuenta; las señales de escucha no (RN-07)."""
    return sorted(i.inicio for i in resultado.interrupciones if i.tipo.cuenta_como_interrupcion)


def cuota_femenina(resultado: Resultado) -> float | None:
    """% del tiempo de habla de las voces femeninas (MD-04)."""
    return next(g.cuota_tiempo for g in resultado.grupos if g.etiqueta is EtiquetaVoz.FEMENINO)


def _sexo_de_quien_mas_coincide(
    turnos: Sequence[Turno], tramos_referencia: Sequence[lectura.Tramo]
) -> dict[int, EtiquetaVoz]:
    """Sexo registrado en AMI de la persona con la que más tiempo coincide cada voz (11.2).

    Una voz que no coincide con nadie de AMI no aparece.
    """
    coincide: dict[int, dict[str, float]] = {}
    for t in turnos:
        for persona, ref_inicio, ref_fin in tramos_referencia:
            comun = min(t.fin, ref_fin) - max(t.inicio, ref_inicio)
            if comun > 0:
                coincide.setdefault(t.hablante, {})
                coincide[t.hablante][persona] = coincide[t.hablante].get(persona, 0.0) + comun
    return {n: lectura.SEXO[max(c, key=c.get)[0]] for n, c in coincide.items()}


def voces_propuestas(
    resultado: Resultado, tramos_referencia: Sequence[lectura.Tramo]
) -> list[metricas.ParVoz]:
    """(Sexo en AMI, propuesta del modelo) de cada voz que etiquetó el modelo (M-02 y M-03).

    Las voces que confirmó una persona no miden el modelo y no entran.
    """
    sexo = _sexo_de_quien_mas_coincide(resultado.turnos, tramos_referencia)
    return [
        (sexo[h.hablante], h.etiqueta)
        for h in sorted(resultado.hablantes, key=lambda h: h.hablante)
        if h.origen is OrigenEtiqueta.MODELO and h.hablante in sexo
    ]


def resultado_ideal(
    tramos_sistema: Sequence[lectura.Tramo],
    tramos_referencia: Sequence[lectura.Tramo],
    config: Config = CONFIG,
) -> Resultado:
    """Resultado del sistema con una confirmación ideal. Solo para medir en AMI.

    En la aplicación una persona confirma cada voz (constitución, regla 8). En AMI nadie confirma,
    así que cada voz de pyannote recibe el sexo de la persona de AMI con la que más tiempo coincide
    (F o M en su código, funcional 11.2). Así M-04 y la ablación miden lo que estropea la separación
    de voces, no el clasificador (eso es M-02 y M-03). No cambia nada del sistema.

    Las voces se numeran por orden de aparición, como en diarizacion.py. Sin fragmentos, solo se
    aplica la regla de los 10 s (RN-01), no la de los 3 tramos limpios (D-18). Una voz que no
    coincide con nadie de AMI queda sin etiqueta: es una voz corta (D-15).
    """
    numero: dict[str, int] = {}
    for codigo, _, _ in sorted(tramos_sistema, key=lambda x: x[1]):
        numero.setdefault(codigo, len(numero) + 1)
    turnos = sorted(
        (Turno(hablante=numero[codigo], inicio=i, fin=f) for codigo, i, f in tramos_sistema),
        key=lambda t: (t.inicio, t.hablante),
    )

    segundos: dict[int, float] = {}
    for t in turnos:
        segundos[t.hablante] = segundos.get(t.hablante, 0.0) + t.fin - t.inicio
    sexo = _sexo_de_quien_mas_coincide(turnos, tramos_referencia)

    etiquetas = [
        EtiquetaConfirmada(hablante=n, etiqueta=sexo[n], origen=OrigenEtiqueta.PERSONA)
        for n in sorted(segundos)
        if segundos[n] >= config.presencia_desde_segundos and n in sexo
    ]
    return analizar(
        EntradaAnalisis(
            duracion=max(t.fin for t in turnos),
            turnos=turnos,
            solapamientos=lectura.solapamientos_de(turnos),
            etiquetas=etiquetas,
        ),
        config,
    )


def evaluar_ami(
    carpeta_ami: Path, salidas: Path, reuniones: Sequence[str] = REUNIONES_PRUEBA
) -> list[Reunion]:
    evaluadas = []
    for nombre in reuniones:
        rttm, json = salidas / f"{nombre}.rttm", salidas / f"{nombre}.json"
        if not (carpeta_ami / f"{nombre}.rttm").exists() or not rttm.exists():
            continue
        tramos = lectura.leer_rttm(carpeta_ami / f"{nombre}.rttm")
        tramos_sistema = lectura.leer_rttm(rttm)
        de_referencia = analizar(lectura.entrada_de_referencia(tramos)[0])
        ideal = not json.exists()  # sin el Resultado del sistema, la confirmación ideal
        sistema = resultado_ideal(tramos_sistema, tramos) if ideal else lectura.leer_resultado(json)
        evaluadas.append(
            Reunion(
                nombre=nombre,
                der=metricas.der(tramos, tramos_sistema),
                error_femenino=metricas.error_porcentaje_femenino(
                    cuota_femenina(de_referencia), cuota_femenina(sistema)
                ),
                ablacion=metricas.deteccion(inicios(sistema), inicios(de_referencia)),
                ideal=ideal,
                voces=() if ideal else tuple(voces_propuestas(sistema, tramos)),
            )
        )
    return evaluadas


def _antes_de(hasta: float, instantes: list[float]) -> list[float]:
    return [x for x in instantes if x < hasta]


def evaluar_grabaciones(carpeta_etiquetas: Path, salidas: Path) -> list[Grabacion]:
    evaluadas = []
    for ruta in sorted(carpeta_etiquetas.glob(f"*{REFERENCIA}")):
        nombre = ruta.name.removesuffix(REFERENCIA)
        json = salidas / f"{nombre}.json"
        if not json.exists():
            continue
        sistema = lectura.leer_resultado(json)
        hasta = ANOTADO_HASTA.get(nombre, float("inf"))
        referencia = _antes_de(hasta, [a.inicio for a in lectura.leer_etiquetas(ruta) if a.cuenta])
        a, c = (carpeta_etiquetas / f"{nombre}_{x}.txt" for x in ("A", "C"))
        kappa = (
            metricas.kappa_entre_anotadoras(lectura.leer_etiquetas(a), lectura.leer_etiquetas(c))
            if a.exists() and c.exists()
            else None
        )
        evaluadas.append(
            Grabacion(
                nombre=nombre,
                sistema=metricas.deteccion(_antes_de(hasta, inicios(sistema)), referencia),
                linea_base=metricas.deteccion(
                    _antes_de(hasta, metricas.linea_base(entrada_del_resultado(sistema))),
                    referencia,
                ),
                kappa=kappa,
            )
        )
    return evaluadas


# --- Informe -------------------------------------------------------------------------------

NO_APLICA = "no aplicable"


def _numero(valor: float | None, formato: Callable[[float], str]) -> str:
    return NO_APLICA if valor is None else formato(valor).replace(".", ",")


def _fila(
    metrica: str,
    unidades: Sequence,
    estadistico: Callable[[list], float | None],
    formato: Callable[[float], str],
) -> str:
    valor = estadistico(list(unidades)) if unidades else None
    intervalo = metricas.intervalo_bootstrap(list(unidades), estadistico=estadistico)
    ic = (
        NO_APLICA
        if valor is None or intervalo is None
        else f"{_numero(intervalo[0], formato)} a {_numero(intervalo[1], formato)}"
    )
    return f"| {metrica} | {_numero(valor, formato)} | {ic} | n = {len(unidades)} |"


def _media(valores: list[float]) -> float | None:
    return sum(valores) / len(valores) if valores else None


def informe(
    reuniones: Sequence[Reunion], grabaciones: Sequence[Grabacion], tiempos: Sequence[float] = ()
) -> str:
    """Tabla de la sección 12.1 en Markdown.

    El IC remuestrea audios enteros, salvo en la voz, donde la unidad es el hablante (11.3).
    """
    con_m04 = [r.error_femenino for r in reuniones if r.error_femenino is not None]
    voces = [par for r in reuniones for par in r.voces]
    puntos = "{:.1f} puntos".format
    con_kappa = [g.kappa for g in grabaciones if g.kappa is not None]
    porcentaje = "{:.1%}".format
    f1 = "{:.2f}".format
    lineas = [
        f"# Evaluación, partición de prueba ({date.today().isoformat()})",
        "",
        "| Métrica | Valor | IC 95 % | n |",
        "| --- | --- | --- | --- |",
        _fila(
            "M-01, DER (reuniones de AMI)",
            [r.der for r in reuniones],
            lambda m: metricas.der_conjunto(m).valor,
            lambda v: porcentaje(v).replace("%", " %"),
        ),
        _fila("M-02, exactitud equilibrada de la voz", voces, metricas.exactitud_equilibrada, f1),
        _fila(
            "M-03, error de la voz femenina",
            voces,
            lambda p: metricas.error_de_grupo(p, EtiquetaVoz.FEMENINO),
            lambda v: f"{v * 100:.1f} %",
        ),
        _fila(
            "M-03, error de la voz masculina",
            voces,
            lambda p: metricas.error_de_grupo(p, EtiquetaVoz.MASCULINO),
            lambda v: f"{v * 100:.1f} %",
        ),
        _fila("M-03, diferencia entre grupos", voces, metricas.diferencia_entre_grupos, puntos),
        _fila("M-04, error del % femenino", con_m04, _media, "{:.2f} puntos".format),
        _fila(
            "M-05, F1 de interrupciones (± 1 s)",
            [g.sistema for g in grabaciones],
            lambda m: metricas.sumar(m).f1,
            f1,
        ),
        _fila(
            "Línea base: cualquier solapamiento",
            [g.linea_base for g in grabaciones],
            lambda m: metricas.sumar(m).f1,
            f1,
        ),
        _fila("M-08, kappa entre anotadoras", con_kappa, _media, f1),
        _fila(
            "Ablación: F1 con pyannote frente a con la referencia de AMI",
            [r.ablacion for r in reuniones if r.ablacion is not None],
            lambda m: metricas.sumar(m).f1,
            f1,
        ),
        _fila(
            "M-09, minutos de proceso por hora de audio (mediana)",
            list(tiempos),
            statistics.median,
            "{:.1f} min".format,
        ),
        "",
        "Con pocos datos, los resultados son orientativos (11.3).",
    ]
    if any(r.ideal for r in reuniones):
        lineas.append(
            "En AMI, M-04 y la ablación usan una confirmación ideal: cada voz de pyannote recibe el "
            "sexo de la persona de AMI con la que más coincide. Miden la separación de voces, no "
            "el clasificador."
        )
    return "\n".join(lineas) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--salidas", type=Path, required=True, help="RTTM y JSON del sistema")
    parser.add_argument("--ami", type=Path, default=AMI, help="RTTM de referencia de AMI")
    parser.add_argument("--etiquetas", type=Path, default=ETIQUETAS, help="etiquetas de Audacity")
    args = parser.parse_args(argv)
    for carpeta in (args.salidas, args.ami, args.etiquetas):
        if not carpeta.is_dir():
            print(f"No existe la carpeta {carpeta}", file=sys.stderr)
            return 2
    print(
        informe(
            evaluar_ami(args.ami, args.salidas),
            evaluar_grabaciones(args.etiquetas, args.salidas),
            cronometrar.leer(args.salidas),
        ),
        end="",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
