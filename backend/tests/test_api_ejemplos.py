"""Ejemplos precalculados (RF-02; spec 003, US4, FR-009): se ven sin confirmación ni audio."""

import shutil

from ayudas import cargar_ejemplo
from conftest import bytes_wav

import contrato as c

IDS = [
    "ejemplo-con-voces-femeninas",
    "ejemplo-muchas-interrupciones",
    "ejemplo-sin-voces-femeninas",
]


def elegir(api, ejemplo):
    return api.cliente.post("/analisis", files={"ejemplo": (None, ejemplo)})


def test_lista_los_ejemplos_ordenados(api):
    respuesta = api.cliente.get("/ejemplos")
    assert respuesta.status_code == 200
    ejemplos = [c.Resultado.model_validate(r) for r in respuesta.json()]
    assert [e.id_analisis for e in ejemplos] == IDS


def test_lee_los_ejemplos_de_su_carpeta(api, tmp_path):
    from api.app import crear_app

    carpeta = tmp_path / "otros"
    carpeta.mkdir()
    shutil.copy(api.ajustes.ejemplos / "sin_voces_femeninas.json", carpeta)
    ajustes = api.ajustes.__class__(carpeta_trabajo=tmp_path / "t", ejemplos=carpeta)
    from fastapi.testclient import TestClient

    cliente = TestClient(crear_app(pasos=api.falsos.pasos(), ajustes=ajustes))
    assert [r["id_analisis"] for r in cliente.get("/ejemplos").json()] == [
        "ejemplo-sin-voces-femeninas"
    ]


def test_elegir_un_ejemplo_lo_deja_terminado_sin_confirmar(api):
    respuesta = elegir(api, "ejemplo-con-voces-femeninas")
    assert respuesta.status_code == 201
    estado = c.EstadoAnalisis.model_validate(respuesta.json())
    assert estado.estado is c.Estado.TERMINADO
    assert api.falsos.llamadas == []  # no se ejecuta ningún paso del pipeline


def test_el_resultado_es_el_del_ejemplo_con_su_propio_identificador(api):
    id_analisis = elegir(api, "ejemplo-con-voces-femeninas").json()["id_analisis"]
    resultado = c.Resultado.model_validate(
        api.cliente.get(f"/analisis/{id_analisis}/resultado").json()
    )
    esperado = cargar_ejemplo("con_voces_femeninas")
    assert resultado.id_analisis == id_analisis
    assert resultado.model_dump(exclude={"id_analisis"}) == esperado.model_dump(
        exclude={"id_analisis"}
    )


def test_un_ejemplo_no_deja_ficheros(api):
    elegir(api, "ejemplo-con-voces-femeninas")
    carpeta = api.ajustes.carpeta_trabajo
    assert not carpeta.exists() or list(carpeta.iterdir()) == []


def test_un_ejemplo_desconocido_da_404(api):
    assert elegir(api, "no-existe").status_code == 404


def test_audio_y_ejemplo_a_la_vez_da_400(api):
    respuesta = api.cliente.post(
        "/analisis",
        files={
            "audio": ("a.wav", bytes_wav(api.tmp_path), "audio/wav"),
            "ejemplo": (None, "ejemplo-con-voces-femeninas"),
        },
    )
    assert respuesta.status_code == 400
    assert list(api.ajustes.carpeta_trabajo.iterdir()) == []


def test_los_ejemplos_de_la_demo_son_ib4002_e_ib4010(api, tmp_path):
    """La carpeta por defecto (backend/ejemplos) tiene los resultados reales que muestra la web."""
    from fastapi.testclient import TestClient

    from api.ajustes import EJEMPLOS_POR_DEFECTO, Ajustes
    from api.app import crear_app

    ajustes = Ajustes(carpeta_trabajo=tmp_path / "t", ejemplos=EJEMPLOS_POR_DEFECTO)
    cliente = TestClient(crear_app(pasos=api.falsos.pasos(), ajustes=ajustes))
    ejemplos = [c.Resultado.model_validate(r) for r in cliente.get("/ejemplos").json()]
    assert [e.id_analisis for e in ejemplos] == ["IB4002", "IB4010"]
    for nombre in ("IB4002", "IB4010"):
        respuesta = cliente.post("/analisis", files={"ejemplo": (None, nombre)})
        assert respuesta.status_code == 201
