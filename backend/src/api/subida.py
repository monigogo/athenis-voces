"""Recepción segura del audio subido (RF-01, RNF-10; spec 003, research decisión 6).

- El formulario multipart se lee por trozos y el audio se escribe directamente en su destino, en
  CARPETA_TRABAJO. No se usa request.form() de Starlette, que guarda una copia en el directorio
  temporal del sistema: esa copia quedaría fuera del borrado de la retención (RF-23).
- El tamaño se corta al pasar el límite, aunque la cabecera Content-Length diga otra cosa.
- El tipo real se mira en los primeros bytes; la extensión y el tipo MIME no cuentan.
- La duración la mide ffprobe, sin shell, con tiempo máximo y la ruta como «file:».
"""

import subprocess
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path

from python_multipart.multipart import MultipartParser, parse_options_header

CAMPO_AUDIO = "audio"
CAMPOS_TEXTO = {"ejemplo", "modo_manual"}
_MAX_TEXTO = 256  # bytes de un campo de texto
_TIEMPO_MAXIMO_FFPROBE = 60


class SubidaRechazada(ValueError):
    """El formulario no se acepta. `codigo` es el estado HTTP que le corresponde."""

    def __init__(self, codigo: int, motivo: str) -> None:
        super().__init__(motivo)
        self.codigo = codigo


@dataclass
class Formulario:
    campos: dict[str, str] = field(default_factory=dict)
    hay_audio: bool = False


def frontera(tipo_contenido: str | None) -> bytes:
    """La frontera de un Content-Type multipart/form-data."""
    tipo, parametros = parse_options_header(tipo_contenido)
    if tipo != b"multipart/form-data" or not parametros.get(b"boundary"):
        raise SubidaRechazada(400, "Hay que enviar un formulario multipart/form-data")
    return parametros[b"boundary"]


async def leer_formulario(
    trozos: AsyncIterator[bytes],
    limite: bytes,
    destino: Path,
    max_bytes: int,
    admite_audio: bool = True,
) -> Formulario:
    """Lee el formulario; el campo «audio» va a `destino` y los de texto, a memoria.

    Si algo no se acepta, borra `destino` y lanza SubidaRechazada. Con `admite_audio` falso (demo
    pública, D-08) un audio se rechaza antes de escribir nada.
    """
    lector = _Lector(destino, max_bytes, admite_audio)
    parser = MultipartParser(limite, lector.callbacks())
    try:
        async for trozo in trozos:
            parser.write(trozo)
        parser.finalize()
    except SubidaRechazada:
        lector.cerrar()
        destino.unlink(missing_ok=True)
        raise
    except Exception as error:  # multipart mal formado o conexión cortada
        lector.cerrar()
        destino.unlink(missing_ok=True)
        raise SubidaRechazada(400, "El formulario está mal formado") from error
    lector.cerrar()
    return lector.formulario


class _Lector:
    """Recibe las piezas del parser y decide adónde va cada una."""

    def __init__(self, destino: Path, max_bytes: int, admite_audio: bool) -> None:
        self.formulario = Formulario()
        self._admite_audio = admite_audio
        self._destino = destino
        self._max_bytes = max_bytes
        self._fichero = None
        self._escritos = 0
        self._cabecera = b""
        self._valor = b""
        self._cabeceras: dict[bytes, bytes] = {}
        self._nombre = ""
        self._texto = b""

    def callbacks(self) -> dict:
        return {
            "on_part_begin": self._empieza,
            "on_header_field": self._campo_cabecera,
            "on_header_value": self._valor_cabecera,
            "on_header_end": self._fin_cabecera,
            "on_headers_finished": self._cabeceras_listas,
            "on_part_data": self._datos,
            "on_part_end": self._termina,
        }

    def cerrar(self) -> None:
        if self._fichero is not None:
            self._fichero.close()
            self._fichero = None

    def _empieza(self) -> None:
        self._cabeceras, self._cabecera, self._valor, self._texto = {}, b"", b"", b""

    def _campo_cabecera(self, datos: bytes, inicio: int, fin: int) -> None:
        self._cabecera += datos[inicio:fin]

    def _valor_cabecera(self, datos: bytes, inicio: int, fin: int) -> None:
        self._valor += datos[inicio:fin]

    def _fin_cabecera(self) -> None:
        self._cabeceras[self._cabecera.strip().lower()] = self._valor.strip()
        self._cabecera, self._valor = b"", b""

    def _cabeceras_listas(self) -> None:
        _, parametros = parse_options_header(self._cabeceras.get(b"content-disposition"))
        self._nombre = parametros.get(b"name", b"").decode("utf-8", "replace")
        es_fichero = b"filename" in parametros
        if self._nombre == CAMPO_AUDIO and es_fichero:
            if not self._admite_audio:
                raise SubidaRechazada(403, "La demo pública no admite subidas")
            if self.formulario.hay_audio:
                raise SubidaRechazada(400, "Solo se admite un audio por análisis")
            self.formulario.hay_audio = True
            self._destino.parent.mkdir(parents=True, exist_ok=True)
            self._fichero = self._destino.open("wb")
        elif self._nombre not in CAMPOS_TEXTO or es_fichero:
            raise SubidaRechazada(400, "El formulario lleva un campo que no se admite")

    def _datos(self, datos: bytes, inicio: int, fin: int) -> None:
        if self._fichero is not None:
            self._escritos += fin - inicio
            if self._escritos > self._max_bytes:
                raise SubidaRechazada(413, "El audio supera el tamaño máximo")
            self._fichero.write(datos[inicio:fin])
        else:
            self._texto += datos[inicio:fin]
            if len(self._texto) > _MAX_TEXTO:
                raise SubidaRechazada(400, "Un campo del formulario es demasiado largo")

    def _termina(self) -> None:
        if self._fichero is not None:
            self.cerrar()
        else:
            self.formulario.campos[self._nombre] = self._texto.decode("utf-8", "replace").strip()


def tipo_real(ruta: Path) -> str | None:
    """«wav», «mp3», «ogg», «flac» o «m4a» según los primeros bytes; None si no es audio."""
    with ruta.open("rb") as fichero:
        cabecera = fichero.read(12)
    if cabecera[:4] == b"RIFF" and cabecera[8:12] == b"WAVE":
        return "wav"
    if cabecera[:4] == b"fLaC":
        return "flac"
    if cabecera[:4] == b"OggS":
        return "ogg"
    if cabecera[4:8] == b"ftyp":
        return "m4a"
    if cabecera[:3] == b"ID3" or (
        len(cabecera) >= 2 and cabecera[0] == 0xFF and cabecera[1] & 0xE0 == 0xE0
    ):
        return "mp3"
    return None


def medir_duracion(ruta: Path) -> float:
    """Duración en segundos según ffprobe. Lanza ValueError si no la puede leer."""
    orden = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        f"file:{ruta}",
    ]
    try:
        salida = subprocess.run(
            orden, capture_output=True, text=True, timeout=_TIEMPO_MAXIMO_FFPROBE, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError("No se pudo medir la duración del audio") from error
    try:
        return float(salida.stdout.strip())
    except ValueError:
        raise ValueError("No se pudo medir la duración del audio") from None
