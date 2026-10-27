"""POST /analisis con un audio: seguridad de la subida (RF-01, RNF-10; spec 003, FR-001 y FR-002).

Lo que se rechaza no crea ningún análisis ni deja ningún fichero (historia 1, escenario 2).
"""

import tempfile

import pytest
from conftest import bytes_wav, subir

import contrato as c
from api.subida import tipo_real

MB = 1024 * 1024


def ficheros(api):
    carpeta = api.ajustes.carpeta_trabajo
    return sorted(p.name for p in carpeta.iterdir()) if carpeta.exists() else []


def test_un_wav_valido_crea_un_analisis_en_cola(api):
    respuesta = subir(api)
    assert respuesta.status_code == 201
    estado = c.EstadoAnalisis.model_validate(respuesta.json())
    assert estado.estado is c.Estado.EN_COLA
    assert len(estado.id_analisis) == 32  # uuid4 en hexadecimal, generado por el sistema


def test_el_fichero_lleva_un_nombre_del_sistema(api):
    id_analisis = subir(api, nombre="Reunión de Ana García.wav").json()["id_analisis"]
    assert f"{id_analisis}.subida" in ficheros(api)
    assert not any("Ana" in nombre for nombre in ficheros(api))


def test_el_nombre_original_no_sale_en_ninguna_respuesta(api):
    respuesta = subir(api, contenido=b"esto no es audio", nombre="Ana García.mp3")
    assert "Ana" not in respuesta.text


def test_un_mp3_que_es_texto_se_rechaza_por_su_contenido(api):
    respuesta = subir(api, contenido=b"hola, esto es un texto", nombre="reunion.mp3")
    assert respuesta.status_code == 415
    assert ficheros(api) == []


def test_mas_de_200_mb_se_rechaza(api, monkeypatch):
    respuesta = api.cliente.post(
        "/analisis",
        content=b"x",
        headers={
            "Content-Type": "multipart/form-data; boundary=limite",
            "Content-Length": str(201 * MB),
        },
    )
    assert respuesta.status_code == 413
    assert ficheros(api) == []


def test_si_la_cabecera_miente_se_corta_al_pasar_el_limite(api, monkeypatch):
    import dataclasses

    import api.app as modulo

    monkeypatch.setattr(modulo, "CONFIG", dataclasses.replace(modulo.CONFIG, subida_max_bytes=MB))
    grande = bytes_wav(api.tmp_path, segundos=40.0)  # unos 1,3 MB

    def cuerpo():  # llega por trozos y sin Content-Length
        yield b"--limite\r\n"
        yield b'Content-Disposition: form-data; name="audio"; filename="a.wav"\r\n'
        yield b"Content-Type: audio/wav\r\n\r\n"
        yield grande
        yield b"\r\n--limite--\r\n"

    respuesta = api.cliente.post(
        "/analisis",
        content=b"".join(cuerpo()),
        headers={
            "Content-Type": "multipart/form-data; boundary=limite",
            "Content-Length": "100",  # miente: el cuerpo es mucho mayor
        },
    )
    assert respuesta.status_code == 413
    assert ficheros(api) == []


def test_sin_content_length_se_rechaza(api):
    def trozos():
        yield b"--limite--\r\n"

    respuesta = api.cliente.post(
        "/analisis",
        content=trozos(),
        headers={"Content-Type": "multipart/form-data; boundary=limite"},
    )
    assert respuesta.status_code == 411


def test_mas_de_60_minutos_se_rechaza(api):
    api.duraciones.segundos = 3600.5
    respuesta = subir(api)
    assert respuesta.status_code == 422
    assert ficheros(api) == []


def test_un_audio_que_ffprobe_no_entiende_se_rechaza(api, monkeypatch):
    def ilegible(ruta):
        raise ValueError("no se puede leer")

    monkeypatch.setattr(api.app.state, "medir_duracion", ilegible)
    respuesta = subir(api)
    assert respuesta.status_code == 422
    assert ficheros(api) == []


def test_sin_audio_ni_ejemplo_se_rechaza(api):
    respuesta = api.cliente.post("/analisis", files={"otro": ("x", b"", "text/plain")})
    assert respuesta.status_code == 400
    assert ficheros(api) == []


def test_sin_multipart_se_rechaza(api):
    respuesta = api.cliente.post("/analisis", json={"audio": "x"})
    assert respuesta.status_code == 400


def test_no_queda_copia_en_el_temporal_del_sistema(api, monkeypatch):
    """T049: el audio va directo a CARPETA_TRABAJO, sin la copia temporal de Starlette."""
    sistema = api.tmp_path / "temporal_del_sistema"
    sistema.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(sistema))
    respuesta = subir(api, contenido=bytes_wav(api.tmp_path, segundos=40.0))  # más de 1 MB
    assert respuesta.status_code == 201
    assert list(sistema.iterdir()) == []
    assert f"{respuesta.json()['id_analisis']}.subida" in ficheros(api)


# --- Tipo real por los primeros bytes (FR-001) -------------------------------------------------


@pytest.mark.parametrize(
    ("cabecera", "tipo"),
    [
        (b"RIFF\x24\x00\x00\x00WAVEfmt ", "wav"),
        (b"ID3\x04\x00\x00\x00\x00\x00\x00\x00\x00", "mp3"),
        (b"\xff\xfb\x90\x00" + b"\x00" * 8, "mp3"),
        (b"OggS\x00\x02" + b"\x00" * 6, "ogg"),
        (b"fLaC\x00\x00\x00\x22" + b"\x00" * 4, "flac"),
        (b"\x00\x00\x00\x20ftypM4A " + b"\x00" * 4, "m4a"),
    ],
)
def test_reconoce_los_formatos_admitidos(tmp_path, cabecera, tipo):
    ruta = tmp_path / "a.subida"
    ruta.write_bytes(cabecera)
    assert tipo_real(ruta) == tipo


@pytest.mark.parametrize(
    "cabecera",
    [b"", b"hola mundo", b"%PDF-1.7\n", b"\x89PNG\r\n\x1a\n", b"RIFF\x00\x00\x00\x00AVI LIST"],
)
def test_rechaza_lo_que_no_es_audio(tmp_path, cabecera):
    ruta = tmp_path / "a.subida"
    ruta.write_bytes(cabecera)
    assert tipo_real(ruta) is None


# --- Demo pública sin subidas (D-08, FR-016) [VALIDAR] -------------------------------------------


@pytest.fixture
def demo(api):
    import dataclasses

    from conftest import EjecutorSincrono
    from fastapi.testclient import TestClient

    from api.app import crear_app

    ajustes = dataclasses.replace(api.ajustes, demo_publica=True)
    app = crear_app(pasos=api.falsos.pasos(), ajustes=ajustes, ejecutor=EjecutorSincrono())
    return TestClient(app), ajustes


def test_la_demo_publica_no_admite_subidas(demo, api):
    cliente, ajustes = demo
    respuesta = cliente.post(
        "/analisis", files={"audio": ("a.wav", bytes_wav(api.tmp_path), "audio/wav")}
    )
    assert respuesta.status_code == 403
    assert not ajustes.carpeta_trabajo.exists() or list(ajustes.carpeta_trabajo.iterdir()) == []
    assert api.falsos.llamadas == []


def test_la_demo_publica_si_ofrece_los_ejemplos(demo):
    cliente, _ = demo
    respuesta = cliente.post("/analisis", files={"ejemplo": (None, "ejemplo-con-voces-femeninas")})
    assert respuesta.status_code == 201
    assert cliente.get("/ejemplos").status_code == 200
