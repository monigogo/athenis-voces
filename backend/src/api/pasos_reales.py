"""Los pasos del pipeline con los módulos reales de las features 001 y 002.

Los modelos (pyannote, inaSpeechSegmenter) se cargan dentro de cada módulo la primera vez que se
usan: importar este fichero no los descarga ni necesita el grupo «audio».
"""

from analisis.analizar import analizar
from audio.diarizacion import diarizar
from audio.fragmentos import elegir_fragmentos
from audio.preparar import preparar
from pipeline import Pasos
from voz.clasificador import proponer_voz


def pasos_reales() -> Pasos:
    return Pasos(
        preparar=preparar,
        diarizar=diarizar,
        proponer_voz=proponer_voz,
        elegir_fragmentos=elegir_fragmentos,
        analizar=analizar,
    )
