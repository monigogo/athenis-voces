"""Umbrales y pesos del sistema, en un solo sitio (plan, Parte 4).

Son los valores iniciales del funcional. Los marcados [VALIDAR] se ajustan solo con la partición de
desarrollo (RD-05) y cada cambio se anota en el anexo C (RD-06). Todos los tiempos van en segundos.

El nombre de cada umbral dice cómo se compara: «mas_de» es estrictamente mayor, «desde» es mayor o
igual, y «en» es como mucho ese tiempo.
"""

from dataclasses import dataclass, fields


@dataclass(frozen=True)
class Config:
    # Presencia: una voz cuenta si suma al menos 10 s (RN-01) [VALIDAR]
    presencia_desde_segundos: float = 10.0
    # Con menos voces presentes no hay nada que comparar: el análisis acaba en «error» (D-17)
    voces_presentes_minimas: int = 2

    # Propuesta de voz: dentro de la zona dudosa se propone «indeterminado» (RF-06) [VALIDAR]
    zona_dudosa_min: float = 0.35
    zona_dudosa_max: float = 0.65

    # Fragmentos para confirmar cada voz (RF-07)
    fragmentos_por_hablante: int = 3
    fragmento_min_segundos: float = 3.0
    fragmento_max_segundos: float = 5.0

    # Posición y turnos largos (MD-06 a MD-08)
    abre_cierra_turno_mas_de: float = 5.0
    turno_largo_mas_de: float = 30.0

    # Interrupciones (catálogo 6.7)
    solapamiento_mas_de: float = 0.3  # B empieza mientras A habla y se pisan más de 0,3 s
    exito_en_segundos: float = 2.0  # «con éxito»: A deja de hablar en los 2 s siguientes
    intento_desde_segundos: float = 1.0  # «intento»: B habla 1 s o más; si no, señal de escucha
    recupera_en_segundos: float = 10.0  # MD-16: vuelve a hablar en 10 s o menos
    segundos_por_tasa: float = 600.0  # RN-08: tasas por cada 10 min de habla

    # Índice de protagonismo (6.7) [VALIDAR]
    peso_participacion: float = 0.5
    peso_posicion: float = 0.25
    peso_turnos_largos: float = 0.25

    # Audio normalizado (RF-03)
    frecuencia_muestreo: int = 16_000
    tolerancia_duracion_segundos: float = 0.1

    # Fragmento para escuchar una interrupción (RF-18, 9.3)
    escucha_antes_max_segundos: float = 1.0
    escucha_max_segundos: float = 15.0  # [VALIDAR]

    # Subida y retención (RF-01, RNF-10, RF-23; spec 003, aclaraciones 1 y 2) [VALIDAR]
    subida_max_bytes: int = 200 * 1024 * 1024
    subida_max_segundos: float = 3600.0
    retencion_segundos: float = 86_400.0  # 24 h desde la subida (D-08)

    def __post_init__(self) -> None:
        pesos = {"peso_participacion", "peso_posicion", "peso_turnos_largos"}
        for campo in fields(self):
            valor = getattr(self, campo.name)
            if campo.name in pesos or campo.name == "zona_dudosa_min":
                if valor < 0:
                    raise ValueError(f"{campo.name} no puede ser negativo")
            elif valor <= 0:
                raise ValueError(f"{campo.name} debe ser mayor que 0")
        if not self.zona_dudosa_min < self.zona_dudosa_max <= 1:
            raise ValueError("la zona dudosa debe cumplir 0 <= mínimo < máximo <= 1")
        if self.fragmento_min_segundos > self.fragmento_max_segundos:
            raise ValueError("el fragmento mínimo no puede superar al máximo")
        if self.escucha_antes_max_segundos >= self.escucha_max_segundos:
            raise ValueError("el margen previo debe caber en el fragmento de escucha")


CONFIG = Config()
