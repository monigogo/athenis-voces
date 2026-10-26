"""Decide si la licencia de cada dependencia es abierta (RNF-18). Lo llama scripts/listar_licencias.sh.

Uso:   python scripts/comprobar_licencias.py <json de pip-licenses con --with-license-file>

Escribe una tabla en Markdown y acaba con código 1 si alguna licencia no es abierta o no consta.
Si un paquete no declara su licencia, se mira el texto de su fichero de licencia.

Excepción (anexo C, D-22): las librerías CUDA de NVIDIA no son abiertas, pero solo sirven para usar
la GPU que cede OVHcloud (constitución, regla 4). Se listan como «permitida (D-22)» y no hacen
fallar. Cualquier otra licencia cerrada sí.
"""

import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path

ABIERTA = "abierta"
ABIERTA_SEGUN_FICHERO = "abierta (según su fichero)"
NO_ABIERTA = "NO abierta"
NO_CONSTA = "NO consta"
PERMITIDA = "permitida (D-22)"

# Solo los paquetes CUDA de NVIDIA (nvidia-<librería>-cu12 y cuda-toolkit): D-22
_CUDA = re.compile(r"^(nvidia-[a-z0-9-]+-cu\d+|cuda-toolkit)$")

_NO_ABIERTAS = re.compile(
    r"proprietary|non-?commercial|eula|nvidia software license", re.IGNORECASE
)
_ABIERTAS = re.compile(
    r"\b(MIT|BSD|0BSD|Apache|ISC|MPL|Mozilla Public|L?GPL|GNU|Python Software Foundation|PSF"
    r"|Unlicense|CC0|Zlib|HPND|Historical Permission|Artistic|EPL|Eclipse Public|BSL-1\.0)\b",
    re.IGNORECASE,
)


def estado(licencia: str, texto: str, nombre: str = "") -> str:
    decision = _estado_de_la_licencia(licencia, texto)
    if decision in (NO_ABIERTA, NO_CONSTA) and _CUDA.match(nombre):
        return PERMITIDA
    return decision


def _estado_de_la_licencia(licencia: str, texto: str) -> str:
    if _NO_ABIERTAS.search(licencia):
        return NO_ABIERTA
    if licencia != "UNKNOWN" and _ABIERTAS.search(licencia):
        return ABIERTA
    # Solo el principio del fichero: el cuerpo de una licencia abierta puede citar otras palabras
    cabecera = "\n".join(texto.splitlines()[:5])
    if _NO_ABIERTAS.search(cabecera):
        return NO_ABIERTA
    if _ABIERTAS.search(cabecera):
        return ABIERTA_SEGUN_FICHERO
    return NO_CONSTA


def main(argv: Sequence[str] | None = None) -> int:
    argumentos = sys.argv[1:] if argv is None else argv
    paquetes = json.loads(Path(argumentos[0]).read_text(encoding="utf-8"))
    print("| Paquete | Versión | Licencia | Estado |")
    print("| --- | --- | --- | --- |")
    malas = permitidas = 0
    for p in sorted(paquetes, key=lambda p: p["Name"].lower()):
        decision = estado(p["License"], p.get("LicenseText", ""), p["Name"])
        malas += decision in (NO_ABIERTA, NO_CONSTA)
        permitidas += decision == PERMITIDA
        print(f"| {p['Name']} | {p['Version']} | {p['License']} | {decision} |")
    print()
    print(f"{malas} de {len(paquetes)} paquetes con una licencia que no es abierta o no consta.")
    print(
        f"{permitidas} de {len(paquetes)} paquetes con licencia cerrada permitida por D-22 (CUDA)."
    )
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
