"""Lectura de los datos de evaluación: RTTM de AMI (anotaciones de BUT) y etiquetas de Audacity."""

from dataclasses import dataclass
from pathlib import Path

from config import CONFIG, Config
from contrato import (
    EntradaAnalisis,
    EtiquetaConfirmada,
    EtiquetaVoz,
    OrigenEtiqueta,
    Resultado,
    Solapamiento,
    Turno,
)

# Tipos de la guía de anotación (evaluacion/guia_anotacion.md); «colaborativo» solo existe ahí (D-16)
TIPOS_ANOTACION = ("con_exito", "intento", "senal_de_escucha", "colaborativo")
# En AMI, la primera letra del código de participante es su sexo registrado (funcional, 11.2)
SEXO = {"F": EtiquetaVoz.FEMENINO, "M": EtiquetaVoz.MASCULINO}

Tramo = tuple[str, float, float]  # (código o número de hablante, inicio, fin), como en un RTTM


@dataclass(frozen=True)
class Anotacion:
    inicio: float
    fin: float
    tipo: str

    @property
    def cuenta(self) -> bool:
        """Solo «con éxito» e «intento» son interrupciones (RN-07, D-16)."""
        return self.tipo in ("con_exito", "intento")


def leer_rttm(ruta: Path) -> list[Tramo]:
    """Tramos (código, inicio, fin) de las líneas SPEAKER, sin los de duración 0."""
    tramos = []
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        partes = linea.split()
        if len(partes) >= 8 and partes[0] == "SPEAKER" and float(partes[4]) > 0:
            inicio = float(partes[3])
            tramos.append((partes[7], inicio, round(inicio + float(partes[4]), 3)))
    return tramos


def entrada_de_referencia(
    tramos: list[Tramo], config: Config = CONFIG
) -> tuple[EntradaAnalisis, dict[int, str]]:
    """Convierte la referencia de AMI en la entrada del análisis.

    Los códigos se numeran por orden alfabético. Igual que en el sistema, solo se etiquetan las voces
    presentes (RN-01); las demás quedan como voces cortas (D-15). Devuelve también número -> código.
    """
    codigos = sorted({codigo for codigo, _, _ in tramos})
    for codigo in codigos:
        if codigo[:1] not in SEXO:
            raise ValueError(f"El código {codigo} no empieza por F ni por M")
    numero = {codigo: n for n, codigo in enumerate(codigos, start=1)}
    turnos = sorted(
        (Turno(hablante=numero[codigo], inicio=i, fin=f) for codigo, i, f in tramos),
        key=lambda t: (t.inicio, t.hablante),
    )
    segundos = {codigo: 0.0 for codigo in codigos}
    for codigo, inicio, fin in tramos:
        segundos[codigo] += fin - inicio

    solapamientos = []
    for k, a in enumerate(turnos):
        for b in turnos[k + 1 :]:
            if b.inicio >= a.fin:
                break
            if a.hablante != b.hablante:
                solapamientos.append(
                    Solapamiento(
                        hablantes=sorted([a.hablante, b.hablante]),
                        inicio=round(b.inicio, 3),
                        fin=round(min(a.fin, b.fin), 3),
                    )
                )

    etiquetas = [
        EtiquetaConfirmada(
            hablante=numero[codigo], etiqueta=SEXO[codigo[0]], origen=OrigenEtiqueta.PERSONA
        )
        for codigo in codigos
        if segundos[codigo] >= config.presencia_desde_segundos
    ]
    entrada = EntradaAnalisis(
        duracion=max(t.fin for t in turnos),
        turnos=turnos,
        solapamientos=solapamientos,
        etiquetas=etiquetas,
    )
    return entrada, {n: codigo for codigo, n in numero.items()}


def leer_resultado(ruta: Path) -> Resultado:
    """Resultado del análisis guardado en JSON (contrato de datos)."""
    return Resultado.model_validate_json(Path(ruta).read_text(encoding="utf-8"))


def leer_etiquetas(ruta: Path) -> list[Anotacion]:
    """Etiquetas exportadas de Audacity: «inicio<TAB>fin<TAB>tipo» por línea.

    Ignora las líneas de frecuencias (empiezan por «\\») y acepta coma decimal.
    """
    ruta = Path(ruta)
    anotaciones = []
    for n, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), start=1):
        if not linea.strip() or linea.startswith("\\"):
            continue
        partes = linea.split("\t")
        if len(partes) < 3:
            raise ValueError(f"{ruta.name}, línea {n}: se esperaban inicio, fin y tipo")
        inicio, fin = (float(x.replace(",", ".")) for x in partes[:2])
        tipo = partes[2].strip()
        if tipo not in TIPOS_ANOTACION:
            raise ValueError(
                f"{ruta.name}, línea {n}: tipo «{tipo}» desconocido; "
                f"usa {', '.join(TIPOS_ANOTACION)}"
            )
        anotaciones.append(Anotacion(inicio, fin, tipo))
    return anotaciones
