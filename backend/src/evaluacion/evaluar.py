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
from contrato import EntradaAnalisis, EtiquetaConfirmada, EtiquetaVoz, Resultado
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
    # interrupciones con pyannote frente a con la referencia de AMI; None sin el .json
    ablacion: metricas.Deteccion | None


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


def evaluar_ami(
    carpeta_ami: Path, salidas: Path, reuniones: Sequence[str] = REUNIONES_PRUEBA
) -> list[Reunion]:
    evaluadas = []
    for nombre in reuniones:
        rttm, json = salidas / f"{nombre}.rttm", salidas / f"{nombre}.json"
        if not (carpeta_ami / f"{nombre}.rttm").exists() or not rttm.exists():
            continue
        tramos = lectura.leer_rttm(carpeta_ami / f"{nombre}.rttm")
        error_femenino, ablacion = None, None  # sin el .json, solo el DER
        if json.exists():
            de_referencia = analizar(lectura.entrada_de_referencia(tramos)[0])
            sistema = lectura.leer_resultado(json)
            error_femenino = metricas.error_porcentaje_femenino(
                cuota_femenina(de_referencia), cuota_femenina(sistema)
            )
            ablacion = metricas.deteccion(inicios(sistema), inicios(de_referencia))
        evaluadas.append(
            Reunion(
                nombre=nombre,
                der=metricas.der(tramos, lectura.leer_rttm(rttm)),
                error_femenino=error_femenino,
                ablacion=ablacion,
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
