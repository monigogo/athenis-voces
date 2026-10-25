"""Fragmentos para escuchar cada voz al confirmarla (RF-07, A13).

Reglas de la spec 001 (FR-006, data-model y research):

- Solo reciben fragmentos las voces con 10 s o más de habla (RN-01).
- Cada fragmento sale de un tramo en el que esa voz habla sola: sin ningún solapamiento.
- Hacen falta sitio para al menos 3 fragmentos de 3 s o más, sin nadie más hablando. Sin él la voz
  no aparece: no es una voz presente y su tiempo cuenta como voz corta (D-18).
- Si la voz tiene 3 tramos limpios o más, cada fragmento sale de un tramo distinto. Si tiene menos,
  los tramos largos se parten en varios fragmentos (decisión del equipo, 25 oct 2026).
- Los fragmentos se eligen repartidos a lo largo de la intervención (principio, mitad y final), sin
  azar, y se recortan a 5 s como mucho por el centro, lejos de los bordes.
- Los fragmentos de una misma voz no comparten ni un segundo.
"""

from config import CONFIG, Config
from contrato import Fragmento, Solapamiento, Turno

Intervalo = tuple[float, float]


def _unir(intervalos: list[Intervalo]) -> list[Intervalo]:
    """Junta los intervalos que se tocan o se pisan, en orden."""
    unidos: list[Intervalo] = []
    for inicio, fin in sorted(intervalos):
        if unidos and inicio <= unidos[-1][1]:
            unidos[-1] = (unidos[-1][0], max(unidos[-1][1], fin))
        else:
            unidos.append((inicio, fin))
    return unidos


def _restar(intervalos: list[Intervalo], quitar: list[Intervalo]) -> list[Intervalo]:
    """Lo que queda de los intervalos tras quitarles otros. Los dos van unidos y en orden."""
    quedan: list[Intervalo] = []
    for inicio, fin in intervalos:
        for q_inicio, q_fin in quitar:
            if q_fin <= inicio or q_inicio >= fin:
                continue
            if q_inicio > inicio:
                quedan.append((inicio, q_inicio))
            inicio = max(inicio, q_fin)
            if inicio >= fin:
                break
        if inicio < fin:
            quedan.append((inicio, fin))
    return quedan


def _repartidos(total: int, cuantos: int) -> list[int]:
    """Índices repartidos de 0 a total - 1: primero, intermedios y último."""
    if cuantos == 1:
        return [0]
    paso = (total - 1) / (cuantos - 1)
    return [int(i * paso + 0.5) for i in range(cuantos)]


def _partir(tramos: list[Intervalo], minimo: float) -> list[Intervalo]:
    """Parte cada tramo en tantos trozos iguales como caben de `minimo` segundos o más."""
    trozos: list[Intervalo] = []
    for inicio, fin in tramos:
        cuantos = int((fin - inicio) // minimo)
        largo = (fin - inicio) / cuantos
        trozos.extend((inicio + k * largo, inicio + (k + 1) * largo) for k in range(cuantos))
    return trozos


def _por_el_centro(tramo: Intervalo, maximo: float) -> Intervalo:
    """El tramo recortado a `maximo` segundos como mucho, quitando lo mismo de cada lado."""
    inicio, fin = tramo
    sobra = max(0.0, (fin - inicio) - maximo) / 2
    return inicio + sobra, fin - sobra


def elegir_fragmentos(
    turnos: list[Turno], solapamientos: list[Solapamiento], config: Config = CONFIG
) -> dict[int, list[Fragmento]]:
    """Fragmentos por número de hablante; solo aparecen las voces presentes (RN-01, D-18)."""
    resultado: dict[int, list[Fragmento]] = {}
    for hablante in sorted({t.hablante for t in turnos}):
        propios = [(t.inicio, t.fin) for t in turnos if t.hablante == hablante]
        if sum(fin - inicio for inicio, fin in propios) < config.presencia_desde_segundos:
            continue
        pisados = _unir([(s.inicio, s.fin) for s in solapamientos if hablante in s.hablantes])
        limpios = [
            tramo
            for tramo in _restar(_unir(propios), pisados)
            if tramo[1] - tramo[0] >= config.fragmento_min_segundos
        ]
        if len(limpios) < config.fragmentos_por_hablante:
            limpios = _partir(limpios, config.fragmento_min_segundos)  # los largos dan varios
        if len(limpios) < config.fragmentos_por_hablante:
            continue
        elegidos = [limpios[i] for i in _repartidos(len(limpios), config.fragmentos_por_hablante)]
        resultado[hablante] = [
            Fragmento(inicio=inicio, fin=fin)
            for inicio, fin in (_por_el_centro(t, config.fragmento_max_segundos) for t in elegidos)
        ]
    return resultado
