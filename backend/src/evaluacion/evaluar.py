"""Evaluación (B12): regenera la tabla de la sección 12.1 desde las referencias y las salidas guardadas.

Uso, desde backend/:

    PYTHONPATH=src uv run --group evaluacion python -m evaluacion.evaluar --salidas <carpeta>

- AMI (M-01, M-04 y la ablación): solo las reuniones de prueba (11.3, RD-05). Por cada una hace
  falta, en la carpeta de salidas, <reunión>.rttm (la separación de voces de pyannote), que basta
  para el DER. M-04 y la ablación necesitan además <reunión>.json (el Resultado del sistema).
- Audios anotados (M-05, su línea base y M-08): en la carpeta de etiquetas, <audio>_referencia.txt
  (el consenso de A y C, guía de anotación 8) y, para la kappa, <audio>_A.txt y <audio>_C.txt. En la
  carpeta de salidas, <audio>.json.

Lo que falta no se evalúa y no cuenta en n. Ninguna salida se usa para ajustar nada (constitución 9).
"""

import argparse
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
from evaluacion import lectura, metricas

REUNIONES_PRUEBA = ("EN2002a", "EN2002c", "ES2004a", "IS1009a", "TS3003a")
RAIZ = Path(__file__).resolve().parents[3]
AMI = RAIZ / "datos" / "ami" / "anotaciones_but" / "only_words" / "rttms" / "test"
ETIQUETAS = RAIZ / "evaluacion" / "etiquetas"
REFERENCIA = "_referencia.txt"


@dataclass(frozen=True)
class Reunion:
    nombre: str
    der: metricas.Der  # M-01
    error_femenino: float | None  # M-04, en puntos
    # interrupciones con pyannote frente a con la referencia de AMI
    ablacion: metricas.Deteccion | None
    ideal: bool = False  # True si M-04 y la ablación usan la confirmación ideal (sin .json)


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
    coincide: dict[int, dict[str, float]] = {}
    for codigo, inicio, fin in tramos_sistema:
        n = numero[codigo]
        segundos[n] = segundos.get(n, 0.0) + fin - inicio
        for persona, ref_inicio, ref_fin in tramos_referencia:
            comun = min(fin, ref_fin) - max(inicio, ref_inicio)
            if comun > 0:
                coincide.setdefault(n, {})
                coincide[n][persona] = coincide[n].get(persona, 0.0) + comun

    etiquetas = [
        EtiquetaConfirmada(
            hablante=n,
            etiqueta=lectura.SEXO[max(coincide[n], key=coincide[n].get)[0]],
            origen=OrigenEtiqueta.PERSONA,
        )
        for n in sorted(segundos)
        if segundos[n] >= config.presencia_desde_segundos and n in coincide
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
            )
        )
    return evaluadas


def evaluar_grabaciones(carpeta_etiquetas: Path, salidas: Path) -> list[Grabacion]:
    evaluadas = []
    for ruta in sorted(carpeta_etiquetas.glob(f"*{REFERENCIA}")):
        nombre = ruta.name.removesuffix(REFERENCIA)
        json = salidas / f"{nombre}.json"
        if not json.exists():
            continue
        sistema = lectura.leer_resultado(json)
        referencia = [a.inicio for a in lectura.leer_etiquetas(ruta) if a.cuenta]
        a, c = (carpeta_etiquetas / f"{nombre}_{x}.txt" for x in ("A", "C"))
        kappa = (
            metricas.kappa_entre_anotadoras(lectura.leer_etiquetas(a), lectura.leer_etiquetas(c))
            if a.exists() and c.exists()
            else None
        )
        evaluadas.append(
            Grabacion(
                nombre=nombre,
                sistema=metricas.deteccion(inicios(sistema), referencia),
                linea_base=metricas.deteccion(
                    metricas.linea_base(entrada_del_resultado(sistema)), referencia
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


def informe(reuniones: Sequence[Reunion], grabaciones: Sequence[Grabacion]) -> str:
    """Tabla de la sección 12.1 en Markdown. El IC remuestrea audios enteros (11.3)."""
    con_m04 = [r.error_femenino for r in reuniones if r.error_femenino is not None]
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
            evaluar_ami(args.ami, args.salidas), evaluar_grabaciones(args.etiquetas, args.salidas)
        ),
        end="",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
