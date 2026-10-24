"""Contrato de datos de athenis-voces: única fuente de los datos que se pasan los módulos (RD-02).

Convenciones (funcional, 9.4): campos en español sin tildes, tiempos en segundos con decimales y
el campo version_contrato en cada mensaje. Los hablantes se numeran desde 1 («Hablante n», RN-10).
En cualquier métrica o índice, None significa «no aplicable» (RN-13), nunca 0.

Este módulo solo define tipos y validaciones: no calcula nada ni importa modelos de audio.
"""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

VERSION_CONTRATO = "0.2"

NumeroHablante = Annotated[int, Field(ge=1)]
Segundos = Annotated[float, Field(ge=0)]
Porcentaje = Annotated[float, Field(ge=0, le=100)]
Recuento = Annotated[int, Field(ge=0)]
Tasa = Annotated[float, Field(ge=0)]  # por cada 10 min de habla (RN-08)


class EtiquetaVoz(StrEnum):
    """Cómo suena una voz. «Indeterminado» nunca se reparte entre las otras dos (RN-03)."""

    FEMENINO = "femenino"
    MASCULINO = "masculino"
    INDETERMINADO = "indeterminado"


class OrigenEtiqueta(StrEnum):
    """Quién fijó la etiqueta final (RF-07)."""

    MODELO = "modelo"
    PERSONA = "persona"


class Estado(StrEnum):
    """Estados de un análisis (RF-04)."""

    EN_COLA = "en_cola"
    PROCESANDO = "procesando"
    ESPERANDO_CONFIRMACION = "esperando_confirmacion"
    TERMINADO = "terminado"
    ERROR = "error"


class TipoSolapamiento(StrEnum):
    """Tipos de solapamiento (funcional, 6.7)."""

    CON_EXITO = "con_exito"
    INTENTO = "intento"
    SENAL_DE_ESCUCHA = "senal_de_escucha"

    @property
    def cuenta_como_interrupcion(self) -> bool:
        """Solo «con éxito» e «intento» cuentan como interrupción (RN-07)."""
        return self is not TipoSolapamiento.SENAL_DE_ESCUCHA


class NombreIndice(StrEnum):
    """Índices de grupo (RF-16). El índice de protagonismo es por persona y va en MetricasHablante."""

    RATIO_REPRESENTACION = "ratio_representacion"
    BRECHA_INTERRUPCION = "brecha_interrupcion"


class Modelo(BaseModel):
    """Base de todos los tipos: rechaza campos desconocidos para detectar errores de nombre."""

    model_config = ConfigDict(extra="forbid")


class Mensaje(Modelo):
    """Base de los mensajes completos que se intercambian (9.4)."""

    version_contrato: str = VERSION_CONTRATO

    @field_validator("version_contrato")
    @classmethod
    def _version_actual(cls, valor: str) -> str:
        if valor != VERSION_CONTRATO:
            raise ValueError(f"version_contrato debe ser {VERSION_CONTRATO}, no {valor}")
        return valor


def _sin_repetidos(valores: list, que: str) -> None:
    if len(valores) != len(set(valores)):
        raise ValueError(f"{que} repetido")


# --- Tiempos ------------------------------------------------------------------------------


class Tramo(Modelo):
    """Intervalo de tiempo del audio, en segundos."""

    inicio: Segundos
    fin: Segundos

    @model_validator(mode="after")
    def _fin_despues_de_inicio(self) -> Self:
        if self.fin <= self.inicio:
            raise ValueError("fin debe ser mayor que inicio")
        return self


class Turno(Tramo):
    """Tramo continuo en el que habla un hablante (RF-05)."""

    hablante: NumeroHablante


class Solapamiento(Tramo):
    """Tramo en el que hablan dos o más hablantes a la vez (RF-05)."""

    hablantes: list[NumeroHablante] = Field(min_length=2)

    @field_validator("hablantes")
    @classmethod
    def _distintos(cls, hablantes: list[int]) -> list[int]:
        _sin_repetidos(hablantes, "hablante")
        return hablantes


class Fragmento(Tramo):
    """Muestra de la voz de un hablante para escucharla al confirmar (RF-07)."""


# --- Voz: propuesta y confirmación (RF-06, RF-07, RF-08) -------------------------------------


class PropuestaVoz(Modelo):
    """Propuesta del modelo para un hablante; la decide una persona (RN-02)."""

    etiqueta: EtiquetaVoz
    confianza: float = Field(ge=0, le=1)


class Hablante(Modelo):
    """Un hablante tal como llega a la pantalla Confirmar voces."""

    hablante: NumeroHablante
    segundos_habla: Segundos
    propuesta: PropuestaVoz | None = None  # None en modo manual (RF-08)
    fragmentos: list[Fragmento]


class HablantesParaConfirmar(Mensaje):
    """Respuesta de GET /analisis/{id}/hablantes (9.3)."""

    id_analisis: str = Field(min_length=1)
    hablantes: list[Hablante]

    @model_validator(mode="after")
    def _sin_hablantes_repetidos(self) -> Self:
        _sin_repetidos([h.hablante for h in self.hablantes], "hablante")
        return self


class EtiquetaConfirmada(Modelo):
    """Etiqueta final de un hablante y quién la fijó (RF-07)."""

    hablante: NumeroHablante
    etiqueta: EtiquetaVoz
    origen: OrigenEtiqueta


class Confirmacion(Mensaje):
    """Cuerpo de POST /analisis/{id}/confirmacion (9.3)."""

    etiquetas: list[EtiquetaConfirmada] = Field(min_length=1)

    @model_validator(mode="after")
    def _sin_hablantes_repetidos(self) -> Self:
        _sin_repetidos([e.hablante for e in self.etiquetas], "hablante")
        return self


# --- Estado (RF-04, RNF-16) ------------------------------------------------------------------


class EstadoAnalisis(Mensaje):
    """Respuesta de GET /analisis/{id} (9.3)."""

    id_analisis: str = Field(min_length=1)
    estado: Estado
    progreso: Porcentaje | None = None  # solo en «procesando»
    motivo_error: str | None = None  # solo en «error», y ahí es obligatorio

    @model_validator(mode="after")
    def _coherente_con_el_estado(self) -> Self:
        procesando = self.estado is Estado.PROCESANDO
        if procesando != (self.progreso is not None):
            raise ValueError("progreso va solo, y siempre, en el estado procesando")
        error = self.estado is Estado.ERROR
        if error != bool(self.motivo_error):
            raise ValueError("motivo_error va solo, y siempre, en el estado error")
        return self


# --- Entrada del análisis ---------------------------------------------------------------------


class EntradaAnalisis(Mensaje):
    """Lo que recibe el análisis: turnos, solapamientos y etiquetas ya confirmadas."""

    duracion: float = Field(gt=0)
    turnos: list[Turno]
    solapamientos: list[Solapamiento]
    etiquetas: list[EtiquetaConfirmada]

    @model_validator(mode="after")
    def _coherente(self) -> Self:
        for tramo in [*self.turnos, *self.solapamientos]:
            if tramo.fin > self.duracion:
                raise ValueError("un tramo acaba después del final del audio")
        con_turnos = {t.hablante for t in self.turnos}
        _sin_repetidos([e.hablante for e in self.etiquetas], "hablante")
        if not {e.hablante for e in self.etiquetas} <= con_turnos:
            raise ValueError("hay una etiqueta de un hablante sin turnos")
        for s in self.solapamientos:
            if not set(s.hablantes) <= con_turnos:
                raise ValueError("hay un solapamiento de un hablante sin turnos")
        return self


# --- Resultado (RF-12 a RF-17) ------------------------------------------------------------


class Interrupcion(Tramo):
    """Solapamiento clasificado entre dos hablantes (RF-14). Incluye las señales de escucha."""

    interrumpe: NumeroHablante
    interrumpido: NumeroHablante
    tipo: TipoSolapamiento

    @model_validator(mode="after")
    def _hablantes_distintos(self) -> Self:
        if self.interrumpe == self.interrumpido:
            raise ValueError("interrumpe e interrumpido deben ser distintos")
        return self


class MetricasHablante(Modelo):
    """Métricas de una persona (catálogo 6.7)."""

    hablante: NumeroHablante
    etiqueta: EtiquetaVoz
    origen: OrigenEtiqueta
    segundos_habla: Segundos
    turnos: Recuento
    turnos_largos: Recuento  # MD-06
    abre: bool  # MD-07
    cierra: bool  # MD-08
    interrupciones_recibidas: Recuento  # MD-14
    interrupciones_hechas: Recuento  # MD-14
    tasa_interrupcion_recibida: Tasa | None = None  # MD-15
    recupera_palabra: Porcentaje | None = None  # MD-16
    apoyos_recibidos: Tasa | None = None  # MD-17
    indice_protagonismo: Porcentaje | None = None  # RF-16, de 0 a 100


class MetricasGrupo(Modelo):
    """Métricas de un grupo de voces (catálogo 6.7)."""

    etiqueta: EtiquetaVoz
    numero_voces: Recuento  # MD-02
    segundos_habla: Segundos
    cuota_tiempo: Porcentaje | None = None  # MD-04
    turnos: Recuento
    cuota_turnos: Porcentaje | None = None  # MD-05
    interrupciones_recibidas: Recuento
    tasa_interrupcion_recibida: Tasa | None = None  # para la BI


class Indice(Modelo):
    """Índice de grupo con su fórmula (RN-06). valor None = «no aplicable» (RN-13)."""

    nombre: NombreIndice
    valor: float | None = Field(ge=0)
    formula: str = Field(min_length=1)

    @property
    def aplicable(self) -> bool:
        return self.valor is not None


class Resultado(Mensaje):
    """Respuesta de GET /analisis/{id}/resultado (9.3)."""

    id_analisis: str = Field(min_length=1)
    duracion: float = Field(gt=0)
    voz_femenina_presente: bool  # MD-01
    primera_intervencion_femenina: Segundos | None = None  # MD-03
    # D-15: segundos de las voces de menos de 10 s, que no cuentan como voz (RN-01)
    segundos_voces_cortas: Segundos
    grupos: list[MetricasGrupo]
    hablantes: list[MetricasHablante]
    turnos: list[Turno]
    solapamientos: list[Solapamiento]
    interrupciones: list[Interrupcion]
    indices: list[Indice]

    @model_validator(mode="after")
    def _sin_duplicados(self) -> Self:
        _sin_repetidos([g.etiqueta for g in self.grupos], "grupo")
        _sin_repetidos([h.hablante for h in self.hablantes], "hablante")
        _sin_repetidos([i.nombre for i in self.indices], "índice")
        return self
