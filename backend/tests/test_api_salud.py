"""GET /salud (funcional, 9.3): el servicio responde."""


def test_salud(api):
    respuesta = api.cliente.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}


def test_publica_la_descripcion_openapi_con_las_rutas_de_9_3(api):  # RD-02
    rutas = set(api.cliente.get("/openapi.json").json()["paths"])
    assert rutas == {
        "/salud",
        "/analisis",
        "/analisis/{id_analisis}",
        "/analisis/{id_analisis}/hablantes",
        "/analisis/{id_analisis}/confirmacion",
        "/analisis/{id_analisis}/resultado",
        "/analisis/{id_analisis}/fragmento",
        "/ejemplos",
    }
