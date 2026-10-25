"""Tests para audio/diarizacion.py (T006).

TDD: estos tests deben fallar antes de que exista la implementación.

El import de pyannote.audio va DENTRO de diarizar(), no al inicio del módulo,
por lo que aquí sólo mockeamos el objeto que devuelve Pipeline.from_pretrained.

Convención de mock:
  - _mock_pipeline_ok(segmentos)  → Pipeline.from_pretrained devuelve un callable
    que, al ser invocado con el fichero WAV, devuelve una anotación con los segmentos
    indicados.
  - Un segmento es (inicio, fin, etiqueta_hablante) en segundos.
"""

import sys
import types
import wave
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _crear_wav(ruta: Path, duracion_s: float = 3.0) -> None:
    """WAV mono 16 kHz con silencio."""
    framerate = 16_000
    nframes = int(framerate * duracion_s)
    with wave.open(str(ruta), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        wf.writeframes(b"\x00\x00" * nframes)


class _Segment:
    """Segmento mínimo compatible con la API de pyannote."""

    def __init__(self, start: float, end: float) -> None:
        self.start = start
        self.end = end


class _Anotacion:
    """Falso de pyannote.core.Annotation: los tramos solo salen con itertracks()."""

    def __init__(self, segmentos: list[tuple[float, float, str]]) -> None:
        self._items = [(_Segment(ini, fin), "A", etiq) for ini, fin, etiq in segmentos]

    def itertracks(self, yield_label: bool = False) -> Any:
        assert yield_label, "hace falta yield_label=True para saber quién habla"
        return iter(self._items)


class _DiarizeOutput:
    """Falso de lo que devuelve community-1 en pyannote 4: la anotación va dentro."""

    def __init__(self, anotacion: _Anotacion) -> None:
        self.speaker_diarization = anotacion


def _anotacion_pyannote(segmentos: list[tuple[float, float, str]]) -> Any:
    """Lo que devuelve el pipeline de pyannote 4.0.7 con speaker-diarization-community-1."""
    return _DiarizeOutput(_Anotacion(segmentos))


def _pipeline_ok(segmentos: list[tuple[float, float, str]]) -> MagicMock:
    """Mock de Pipeline.from_pretrained que devuelve segmentos fijos."""
    anotacion = _anotacion_pyannote(segmentos)
    pipeline = MagicMock()
    pipeline.return_value = anotacion
    pipeline.to = MagicMock(return_value=pipeline)
    return pipeline


# ---------------------------------------------------------------------------
# Parche común: evitar que el import real de pyannote ocurra
# ---------------------------------------------------------------------------

_PATCH_PIPELINE = "audio.diarizacion._cargar_pipeline"


class _Tensor:
    """Falso de un tensor de torch: apunta las operaciones que se le piden."""

    def __init__(self, datos: bytes, operaciones: tuple[str, ...] = ()) -> None:
        self.datos = datos
        self.operaciones = operaciones

    def _con(self, operacion: str) -> "_Tensor":
        return _Tensor(self.datos, (*self.operaciones, operacion))

    def float(self) -> "_Tensor":
        return self._con("float")

    def div(self, divisor: float) -> "_Tensor":
        return self._con(f"div({divisor:g})")

    def unsqueeze(self, dimension: int) -> "_Tensor":
        return self._con(f"unsqueeze({dimension})")


class _Torch(types.ModuleType):
    """Falso de torch: solo lo que usan la carga del modelo y la lectura del audio."""

    int16 = "int16"

    def __init__(self, hay_gpu: bool) -> None:
        super().__init__("torch")
        self.cuda = types.SimpleNamespace(is_available=lambda: hay_gpu)

    @staticmethod
    def device(nombre: str) -> str:
        return f"device({nombre})"

    @staticmethod
    def frombuffer(datos: bytearray, dtype: str) -> _Tensor:
        return _Tensor(bytes(datos), (f"frombuffer({dtype})",))


# ---------------------------------------------------------------------------
# RF-05: resultado básico con ≥ 2 hablantes
# ---------------------------------------------------------------------------


def test_diarizar_devuelve_turnos_y_solapamientos(tmp_path: Path) -> None:
    """Con ≥ 2 hablantes devuelve list[Turno] y list[Solapamiento] válidos."""
    from audio.diarizacion import diarizar

    wav = tmp_path / "audio.wav"
    _crear_wav(wav, duracion_s=5.0)

    segmentos = [
        (0.0, 2.0, "SPEAKER_00"),
        (2.5, 4.5, "SPEAKER_01"),
    ]
    with patch(_PATCH_PIPELINE, return_value=_pipeline_ok(segmentos)):
        turnos, solapamientos = diarizar(wav)

    assert len(turnos) == 2, "debe haber dos turnos"
    assert isinstance(solapamientos, list)

    # Verificar tipos del contrato
    from contrato import Solapamiento, Turno

    for t in turnos:
        assert isinstance(t, Turno)
    for s in solapamientos:
        assert isinstance(s, Solapamiento)


# ---------------------------------------------------------------------------
# Sin filtro de duración en solapamientos
# ---------------------------------------------------------------------------


def test_diarizar_solapamientos_muy_cortos_se_incluyen(tmp_path: Path) -> None:
    """Solapamientos de cualquier duración se devuelven sin filtrar."""
    from audio.diarizacion import diarizar

    wav = tmp_path / "audio.wav"
    _crear_wav(wav, duracion_s=6.0)

    # Dos hablantes se solapan 0.05 s (muy por debajo del filtro de la persona B de 0.3 s)
    segmentos = [
        (0.0, 3.0, "SPEAKER_00"),
        (2.95, 5.0, "SPEAKER_01"),  # solapamiento de 0.05 s con SPEAKER_00
    ]
    with patch(_PATCH_PIPELINE, return_value=_pipeline_ok(segmentos)):
        _turnos, solapamientos = diarizar(wav)

    assert len(solapamientos) >= 1, "solapamientos muy cortos no deben filtrarse"


# ---------------------------------------------------------------------------
# Cero o un hablante: no lanza excepción, devuelve los datos detectados
# ---------------------------------------------------------------------------


def test_diarizar_sin_hablantes_devuelve_listas_vacias(tmp_path: Path) -> None:
    """Con cero hablantes devuelve listas vacías sin lanzar excepción."""
    from audio.diarizacion import diarizar

    wav = tmp_path / "silencio.wav"
    _crear_wav(wav, duracion_s=2.0)

    with patch(_PATCH_PIPELINE, return_value=_pipeline_ok([])):
        turnos, solapamientos = diarizar(wav)

    assert turnos == []
    assert solapamientos == []


def test_diarizar_un_hablante_no_lanza_excepcion(tmp_path: Path) -> None:
    """Con un solo hablante devuelve los turnos y lista vacía de solapamientos."""
    from audio.diarizacion import diarizar

    wav = tmp_path / "audio.wav"
    _crear_wav(wav, duracion_s=4.0)

    segmentos = [(0.5, 3.5, "SPEAKER_00")]
    with patch(_PATCH_PIPELINE, return_value=_pipeline_ok(segmentos)):
        turnos, solapamientos = diarizar(wav)

    assert len(turnos) == 1
    assert solapamientos == []


# ---------------------------------------------------------------------------
# Numeración estable 1, 2, 3 por orden de primera aparición
# ---------------------------------------------------------------------------


def test_diarizar_numeracion_por_orden_de_aparicion(tmp_path: Path) -> None:
    """Los hablantes se numeran 1, 2, 3 según el orden en que aparecen por primera vez."""
    from audio.diarizacion import diarizar

    wav = tmp_path / "audio.wav"
    _crear_wav(wav, duracion_s=9.0)

    # SPEAKER_01 aparece primero, luego SPEAKER_00, luego SPEAKER_02
    segmentos = [
        (0.0, 2.0, "SPEAKER_01"),
        (3.0, 5.0, "SPEAKER_00"),
        (6.0, 8.0, "SPEAKER_02"),
    ]
    with patch(_PATCH_PIPELINE, return_value=_pipeline_ok(segmentos)):
        turnos, _ = diarizar(wav)

    # El primer tramo (SPEAKER_01) debe recibir hablante=1
    primer_turno = min(turnos, key=lambda t: t.inicio)
    assert primer_turno.hablante == 1, "el hablante que aparece primero debe ser el 1"

    numeros = {t.hablante for t in turnos}
    assert numeros == {1, 2, 3}, "deben asignarse los números 1, 2 y 3"


def test_diarizar_numeracion_estable_mismo_audio(tmp_path: Path) -> None:
    """Llamar diarizar dos veces con el mismo audio produce la misma numeración."""
    from audio.diarizacion import diarizar

    wav = tmp_path / "audio.wav"
    _crear_wav(wav, duracion_s=5.0)

    segmentos = [
        (0.0, 2.0, "SPEAKER_00"),
        (2.5, 4.5, "SPEAKER_01"),
    ]
    pipeline_mock = _pipeline_ok(segmentos)

    def _nueva_anotacion(*_args: Any, **_kwargs: Any) -> Any:
        return _anotacion_pyannote(segmentos)

    pipeline_mock.side_effect = _nueva_anotacion

    with patch(_PATCH_PIPELINE, return_value=pipeline_mock):
        turnos_a, _ = diarizar(wav)
        turnos_b, _ = diarizar(wav)

    numeros_a = {t.hablante for t in turnos_a}
    numeros_b = {t.hablante for t in turnos_b}
    assert numeros_a == numeros_b, "la numeración debe ser estable entre llamadas"


# ---------------------------------------------------------------------------
# Tramos de duración cero descartados
# ---------------------------------------------------------------------------


def test_diarizar_descarta_tramos_duracion_cero(tmp_path: Path) -> None:
    """Tramos con inicio == fin (duración 0) son descartados silenciosamente."""
    from audio.diarizacion import diarizar

    wav = tmp_path / "audio.wav"
    _crear_wav(wav, duracion_s=5.0)

    segmentos = [
        (0.0, 2.0, "SPEAKER_00"),
        (2.0, 2.0, "SPEAKER_01"),  # duración 0 → debe descartarse
        (3.0, 5.0, "SPEAKER_01"),
    ]
    with patch(_PATCH_PIPELINE, return_value=_pipeline_ok(segmentos)):
        turnos, _ = diarizar(wav)

    duraciones = [t.fin - t.inicio for t in turnos]
    assert all(d > 0 for d in duraciones), "ningún turno debe tener duración 0"


# ---------------------------------------------------------------------------
# Fallo de carga del modelo / HF_TOKEN ausente
# ---------------------------------------------------------------------------


def test_diarizar_falla_carga_modelo_lanza_excepcion_clara(tmp_path: Path) -> None:
    """Si el modelo no carga (p. ej. falta HF_TOKEN), se lanza excepción con motivo."""
    from audio.diarizacion import diarizar

    wav = tmp_path / "audio.wav"
    _crear_wav(wav, duracion_s=2.0)

    with (
        patch(_PATCH_PIPELINE, side_effect=OSError("modelo no encontrado")),
        pytest.raises(Exception) as exc_info,
    ):
        diarizar(wav)

    mensaje = str(exc_info.value)
    assert len(mensaje) > 0, "la excepción debe tener un mensaje no vacío"


def test_diarizar_excepcion_no_expone_hf_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """El mensaje de la excepción no incluye el valor de HF_TOKEN."""
    from audio.diarizacion import diarizar

    token_secreto = "hf_SECRETO_TOKEN_12345"
    monkeypatch.setenv("HF_TOKEN", token_secreto)

    wav = tmp_path / "audio.wav"
    _crear_wav(wav, duracion_s=2.0)

    with (
        patch(_PATCH_PIPELINE, side_effect=OSError("fallo de autenticación")),
        pytest.raises(Exception) as exc_info,
    ):
        diarizar(wav)

    assert token_secreto not in str(exc_info.value), (
        "el mensaje de excepción no debe incluir el valor de HF_TOKEN"
    )


# ---------------------------------------------------------------------------
# No devuelve embeddings ni huellas de voz (RD-04)
# ---------------------------------------------------------------------------


def test_diarizar_no_devuelve_embeddings(tmp_path: Path) -> None:
    """diarizar() devuelve solo (list[Turno], list[Solapamiento]); sin embeddings."""
    from audio.diarizacion import diarizar

    wav = tmp_path / "audio.wav"
    _crear_wav(wav, duracion_s=4.0)

    segmentos = [
        (0.0, 2.0, "SPEAKER_00"),
        (2.5, 4.0, "SPEAKER_01"),
    ]
    with patch(_PATCH_PIPELINE, return_value=_pipeline_ok(segmentos)):
        resultado = diarizar(wav)

    assert isinstance(resultado, tuple), "debe devolver una tupla"
    assert len(resultado) == 2, "la tupla debe tener exactamente dos elementos"

    turnos, solapamientos = resultado
    assert isinstance(turnos, list)
    assert isinstance(solapamientos, list)
    # Sin campos extra que indiquen embeddings en los Turno
    from contrato import Turno

    campos = set(Turno.model_fields.keys())
    assert "embedding" not in campos
    assert "huella" not in campos


# ---------------------------------------------------------------------------
# pyannote 4 también puede devolver la anotación sin envolver
# ---------------------------------------------------------------------------


def test_diarizar_acepta_una_anotacion_sin_envolver(tmp_path: Path) -> None:
    """apply() de pyannote 4 devuelve DiarizeOutput o Annotation: se aceptan los dos."""
    from audio.diarizacion import diarizar

    wav = tmp_path / "audio.wav"
    _crear_wav(wav, duracion_s=5.0)

    pipeline = _pipeline_ok([])
    pipeline.return_value = _Anotacion([(0.0, 2.0, "SPEAKER_00"), (2.5, 4.5, "SPEAKER_01")])
    with patch(_PATCH_PIPELINE, return_value=pipeline):
        turnos, _ = diarizar(wav)

    assert len(turnos) == 2


# ---------------------------------------------------------------------------
# Carga del modelo con la API real de pyannote 4.0.7
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def torch_falso(monkeypatch: pytest.MonkeyPatch) -> None:
    """torch no está en la CI rápida (grupo audio): todas las pruebas usan el falso."""
    monkeypatch.setitem(sys.modules, "torch", _Torch(hay_gpu=False))


@pytest.fixture
def pyannote_falso(monkeypatch: pytest.MonkeyPatch) -> Callable[..., MagicMock]:
    """Sustituye pyannote.audio y torch por falsos y devuelve el pipeline cargado."""

    def instalar(hay_gpu: bool = False) -> MagicMock:
        pipeline = MagicMock()
        modulo = types.ModuleType("pyannote.audio")
        modulo.Pipeline = MagicMock()  # type: ignore[attr-defined]
        modulo.Pipeline.from_pretrained.return_value = pipeline  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "pyannote.audio", modulo)
        monkeypatch.setitem(sys.modules, "torch", _Torch(hay_gpu))
        return modulo.Pipeline.from_pretrained  # type: ignore[attr-defined]

    return instalar


def test_carga_el_modelo_con_token(
    pyannote_falso: Callable[..., MagicMock], monkeypatch: pytest.MonkeyPatch
) -> None:
    """pyannote 4.0.7 ya no acepta use_auth_token: el parámetro se llama token."""
    from audio.diarizacion import _cargar_pipeline

    monkeypatch.setenv("HF_TOKEN", "hf_prueba")
    monkeypatch.delenv("DISPOSITIVO", raising=False)
    from_pretrained = pyannote_falso()
    _cargar_pipeline()

    from_pretrained.assert_called_once_with(
        "pyannote/speaker-diarization-community-1", token="hf_prueba"
    )


@pytest.mark.parametrize(
    ("valor", "hay_gpu", "esperado"),
    [
        (None, True, "cuda"),  # por defecto, auto: la GPU si la hay
        (None, False, "cpu"),  # y si no, la CPU (FR-011, RNF-20)
        ("auto", True, "cuda"),
        ("cpu", True, "cpu"),  # se puede forzar la CPU aunque haya GPU
        ("cuda", True, "cuda"),
        (" CUDA ", True, "cuda"),
    ],
)
def test_elegir_dispositivo(valor: str | None, hay_gpu: bool, esperado: str) -> None:
    from audio.diarizacion import elegir_dispositivo

    assert elegir_dispositivo(valor, hay_gpu) == esperado


def test_pedir_gpu_sin_gpu_da_un_error_claro() -> None:
    """Sin pasar a la CPU en silencio: se mediría otra cosa (RNF-01)."""
    from audio.diarizacion import elegir_dispositivo

    with pytest.raises(RuntimeError, match="no hay GPU"):
        elegir_dispositivo("cuda", hay_gpu=False)


def test_dispositivo_desconocido_dice_las_opciones() -> None:
    from audio.diarizacion import elegir_dispositivo

    with pytest.raises(ValueError, match="auto, cpu o cuda"):
        elegir_dispositivo("gpu", hay_gpu=True)


@pytest.mark.parametrize(("hay_gpu", "esperado"), [(True, "cuda"), (False, "cpu")])
def test_el_modelo_va_al_dispositivo_elegido(
    pyannote_falso: Callable[..., MagicMock],
    monkeypatch: pytest.MonkeyPatch,
    hay_gpu: bool,
    esperado: str,
) -> None:
    from audio.diarizacion import _cargar_pipeline

    monkeypatch.delenv("DISPOSITIVO", raising=False)
    pyannote_falso(hay_gpu=hay_gpu)
    pipeline = _cargar_pipeline()

    pipeline.to.assert_called_once_with(f"device({esperado})")


def test_la_variable_dispositivo_manda(
    pyannote_falso: Callable[..., MagicMock], monkeypatch: pytest.MonkeyPatch
) -> None:
    from audio.diarizacion import _cargar_pipeline

    monkeypatch.setenv("DISPOSITIVO", "cpu")
    pyannote_falso(hay_gpu=True)
    pipeline = _cargar_pipeline()

    pipeline.to.assert_called_once_with("device(cpu)")


def test_dispositivo_mal_escrito_falla_antes_de_descargar_el_modelo(
    pyannote_falso: Callable[..., MagicMock], monkeypatch: pytest.MonkeyPatch
) -> None:
    from audio.diarizacion import _cargar_pipeline

    monkeypatch.setenv("DISPOSITIVO", "gpu")
    from_pretrained = pyannote_falso(hay_gpu=True)
    with pytest.raises(ValueError, match="auto, cpu o cuda"):
        _cargar_pipeline()
    from_pretrained.assert_not_called()


# ---------------------------------------------------------------------------
# El audio se lee en memoria: pyannote no necesita torchcodec ni FFmpeg
# ---------------------------------------------------------------------------


def test_el_pipeline_recibe_el_audio_cargado_y_no_la_ruta(tmp_path: Path) -> None:
    """Con torchcodec roto (OVH) pyannote no puede abrir la ruta: se le da el audio ya leído."""
    from audio.diarizacion import diarizar

    wav = tmp_path / "audio.wav"
    _crear_wav(wav, duracion_s=2.0)
    pipeline = _pipeline_ok([(0.0, 1.0, "SPEAKER_00"), (1.0, 2.0, "SPEAKER_01")])
    with patch(_PATCH_PIPELINE, return_value=pipeline):
        diarizar(wav)

    (entrada,), _ = pipeline.call_args
    assert set(entrada) == {"waveform", "sample_rate"}
    assert entrada["sample_rate"] == 16_000


def test_la_onda_son_las_muestras_del_wav_normalizadas(tmp_path: Path) -> None:
    from audio.diarizacion import _cargar_audio

    wav = tmp_path / "audio.wav"
    _crear_wav(wav, duracion_s=0.5)
    entrada = _cargar_audio(wav)

    onda = entrada["waveform"]
    assert len(onda.datos) == 8_000 * 2  # 0,5 s a 16 kHz, 16 bits
    assert onda.operaciones == (
        "frombuffer(int16)",  # las muestras tal cual
        "float",
        "div(32768)",  # de -1 a 1
        "unsqueeze(0)",  # (canal, tiempo), mono
    )


@pytest.mark.parametrize(
    ("canales", "bytes_por_muestra", "frecuencia"),
    [(2, 2, 16_000), (1, 2, 44_100), (1, 1, 16_000)],
)
def test_un_wav_que_no_es_mono_16_khz_16_bits_se_rechaza(
    tmp_path: Path, canales: int, bytes_por_muestra: int, frecuencia: int
) -> None:
    """preparar.py lo deja en este formato (RF-03); otro formato es un error de quien llama."""
    from audio.diarizacion import _cargar_audio

    wav = tmp_path / "raro.wav"
    with wave.open(str(wav), "w") as f:
        f.setnchannels(canales)
        f.setsampwidth(bytes_por_muestra)
        f.setframerate(frecuencia)
        f.writeframes(b"\x00" * bytes_por_muestra * canales * frecuencia)

    with pytest.raises(ValueError, match="mono"):
        _cargar_audio(wav)


def test_un_wav_sin_muestras_se_rechaza(tmp_path: Path) -> None:
    from audio.diarizacion import _cargar_audio

    wav = tmp_path / "vacio.wav"
    _crear_wav(wav, duracion_s=0.0)

    with pytest.raises(ValueError, match="no tiene muestras"):
        _cargar_audio(wav)
