"""Servidor HTTP de la API interna (funcional, 9.3; spec 003).

Une la web con el núcleo que ya existe: pipeline.py y los módulos reales. No calcula nada: recibe,
valida, encola y guarda el estado. Recibe y devuelve tipos de contrato.py, que no cambia.

Se arranca con un solo proceso (sin --workers): el registro vive en su memoria.

    uv run --env-file ../.env uvicorn api.app:app --app-dir src --port 8000
"""

import threading
import uuid
from collections.abc import Callable
from concurrent.futures import Executor
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from api import retencion
from api.ajustes import Ajustes, desde_entorno
from api.cola import Cola
from api.fragmento import recortar
from api.registro import Analisis, AnalisisDesconocido, Registro
from api.retencion import borrar_caducados, en_marcha
from api.subida import SubidaRechazada, frontera, leer_formulario, medir_duracion, tipo_real
from config import CONFIG
from contrato import Confirmacion, Estado, EstadoAnalisis, HablantesParaConfirmar, Resultado
from pipeline import _AVANCE, Pasos

MARGEN_FORMULARIO = 64 * 1024  # bytes del multipart que no son el audio

_CUERPO_SUBIDA = {
    "requestBody": {
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "audio": {"type": "string", "format": "binary"},
                        "modo_manual": {"type": "boolean", "default": False},
                        "ejemplo": {"type": "string"},
                    },
                }
            }
        },
    }
}


def _si_o_no(valor: str) -> bool:
    if valor.lower() not in ("true", "false"):
        raise SubidaRechazada(400, "modo_manual tiene que ser true o false")
    return valor.lower() == "true"


class EstadoServicio(BaseModel):
    """Respuesta de GET /salud. Es del servicio, no del análisis: no va en el contrato."""

    estado: str = "ok"


def crear_app(
    pasos: Pasos | None = None,
    ajustes: Ajustes | None = None,
    ejecutor: Executor | None = None,
    reloj: Callable[[], datetime] | None = None,
    medir_duracion: Callable[[Path], float] = medir_duracion,
) -> FastAPI:
    if pasos is None:
        from api.pasos_reales import pasos_reales

        pasos = pasos_reales()
    ajustes = ajustes or desde_entorno()
    reloj = reloj or (lambda: datetime.now(UTC))
    registro = Registro()
    cola = Cola(registro, pasos, ajustes.carpeta_trabajo, ejecutor)

    def borrar() -> None:
        borrar_caducados(registro, ajustes.carpeta_trabajo, reloj())

    @asynccontextmanager
    async def vida(app: FastAPI):
        parar = threading.Event()
        app.state.hilo_retencion = en_marcha(borrar, parar)  # RF-23
        yield
        parar.set()

    app = FastAPI(title="athenis-voces", version="0.2", lifespan=vida)
    app.state.medir_duracion = medir_duracion
    app.state.borrar_caducados = borrar

    def buscar(id_analisis: str) -> Analisis:
        try:
            return registro.obtener(id_analisis)
        except AnalisisDesconocido:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese análisis") from None

    def con_audio(analisis: Analisis) -> Analisis:
        if analisis.caducado:  # RF-23: el audio ya se borró
            raise HTTPException(status.HTTP_410_GONE, retencion.MOTIVO)
        return analisis

    @app.get("/salud")
    def salud() -> EstadoServicio:
        return EstadoServicio()

    @app.post("/analisis", status_code=status.HTTP_201_CREATED, openapi_extra=_CUERPO_SUBIDA)
    async def crear_analisis(request: Request) -> EstadoAnalisis:
        """Sube un audio (o elige un ejemplo) y crea el análisis."""
        try:
            return await _crear(request)
        except SubidaRechazada as rechazo:
            raise HTTPException(rechazo.codigo, str(rechazo)) from None

    async def _crear(request: Request) -> EstadoAnalisis:
        longitud = request.headers.get("content-length")
        if longitud is None:
            raise SubidaRechazada(status.HTTP_411_LENGTH_REQUIRED, "Falta Content-Length")
        if not longitud.isdigit() or int(longitud) > CONFIG.subida_max_bytes + MARGEN_FORMULARIO:
            raise SubidaRechazada(413, "El audio supera el tamaño máximo")
        limite = frontera(request.headers.get("content-type"))

        id_analisis = uuid.uuid4().hex  # nombre generado por el sistema (RNF-10)
        audio = ajustes.carpeta_trabajo / f"{id_analisis}.subida"
        formulario = await leer_formulario(
            request.stream(),
            limite,
            audio,
            CONFIG.subida_max_bytes,
            admite_audio=not ajustes.demo_publica,  # D-08 [VALIDAR]
        )
        ejemplo = formulario.campos.get("ejemplo")
        if formulario.hay_audio == bool(ejemplo):
            audio.unlink(missing_ok=True)
            raise SubidaRechazada(400, "Hay que enviar un audio o elegir un ejemplo, no las dos")
        if ejemplo:
            return _desde_ejemplo(id_analisis, ejemplo)
        try:
            modo_manual = _si_o_no(formulario.campos.get("modo_manual", "false"))
            await run_in_threadpool(_comprobar_audio, audio)
        except SubidaRechazada:
            audio.unlink(missing_ok=True)
            raise

        estado = EstadoAnalisis(id_analisis=id_analisis, estado=Estado.EN_COLA)
        registro.crear(
            Analisis(
                id_analisis=id_analisis,
                creado_en=reloj(),
                estado=estado,
                modo_manual=modo_manual,  # RF-08: el clasificador no se ejecuta
                audio=audio,
            )
        )
        cola.fase1(id_analisis)
        return estado

    def _desde_ejemplo(id_analisis: str, nombre: str) -> EstadoAnalisis:
        """Los ejemplos son resultados ya calculados: se saltan la confirmación (8.1)."""
        ejemplo = next((r for r in _ejemplos() if r.id_analisis == nombre), None)
        if ejemplo is None:
            raise SubidaRechazada(status.HTTP_404_NOT_FOUND, "No existe ese ejemplo")
        estado = EstadoAnalisis(id_analisis=id_analisis, estado=Estado.TERMINADO)
        registro.crear(
            Analisis(
                id_analisis=id_analisis,
                creado_en=reloj(),
                estado=estado,
                resultado=ejemplo.model_copy(update={"id_analisis": id_analisis}),
                es_ejemplo=True,
            )
        )
        return estado

    def _ejemplos() -> list[Resultado]:
        """Los Resultado de EJEMPLOS_DIR, ordenados por identificador (RF-02)."""
        ficheros = ajustes.ejemplos.glob("*.json") if ajustes.ejemplos.is_dir() else []
        ejemplos = [Resultado.model_validate_json(f.read_text(encoding="utf-8")) for f in ficheros]
        return sorted(ejemplos, key=lambda r: r.id_analisis)

    @app.get("/ejemplos")
    def listar_ejemplos() -> list[Resultado]:
        return _ejemplos()

    def _comprobar_audio(audio: Path) -> None:
        if tipo_real(audio) is None:
            raise SubidaRechazada(415, "El fichero no es un audio mp3, wav, m4a, ogg o flac")
        try:
            segundos = app.state.medir_duracion(audio)
        except ValueError:
            raise SubidaRechazada(422, "No se puede leer la duración del audio") from None
        if segundos > CONFIG.subida_max_segundos:
            raise SubidaRechazada(422, "El audio supera la duración máxima")

    @app.get("/analisis/{id_analisis}")
    def consultar(id_analisis: str) -> EstadoAnalisis:
        return buscar(id_analisis).estado

    @app.get("/analisis/{id_analisis}/hablantes")
    def hablantes(id_analisis: str) -> HablantesParaConfirmar:
        analisis = con_audio(buscar(id_analisis))
        if analisis.estado.estado is not Estado.ESPERANDO_CONFIRMACION or analisis.confirmado:
            raise HTTPException(status.HTTP_409_CONFLICT, "El análisis no espera confirmación")
        return analisis.preparado.hablantes

    @app.post("/analisis/{id_analisis}/confirmacion", status_code=status.HTTP_202_ACCEPTED)
    def confirmar(id_analisis: str, confirmacion: Confirmacion) -> EstadoAnalisis:
        analisis = buscar(id_analisis)
        with registro.cerrojo:
            if analisis.estado.estado is not Estado.ESPERANDO_CONFIRMACION or analisis.confirmado:
                raise HTTPException(status.HTTP_409_CONFLICT, "El análisis no espera confirmación")
            presentes = {h.hablante for h in analisis.preparado.hablantes.hablantes}
            confirmados = {e.hablante for e in confirmacion.etiquetas}
            if confirmados != presentes:  # RF-07: justo las voces presentes
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_CONTENT,
                    f"Hay que confirmar justo las voces presentes {sorted(presentes)}",
                )
            analisis.confirmado = True
            analisis.estado = EstadoAnalisis(
                id_analisis=id_analisis, estado=Estado.PROCESANDO, progreso=_AVANCE["analizar"]
            )
            estado = analisis.estado
        cola.fase2(id_analisis, confirmacion)
        return estado

    @app.get("/analisis/{id_analisis}/resultado")
    def resultado(id_analisis: str) -> Resultado:
        analisis = buscar(id_analisis)
        if analisis.estado.estado is not Estado.TERMINADO or analisis.resultado is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "El análisis no ha terminado")
        return analisis.resultado

    @app.get(
        "/analisis/{id_analisis}/fragmento",
        response_class=Response,
        responses={200: {"content": {"audio/wav": {}}}},
    )
    def fragmento(id_analisis: str, inicio: float, fin: float) -> Response:
        """Un tramo del audio, 15 s como máximo (9.3)."""
        analisis = con_audio(buscar(id_analisis))
        if analisis.preparado is None or analisis.wav is None or not analisis.wav.exists():
            raise HTTPException(status.HTTP_409_CONFLICT, "El audio todavía no está preparado")
        if (
            inicio < 0
            or fin <= inicio
            or fin - inicio > CONFIG.escucha_max_segundos
            or fin > analisis.preparado.duracion
        ):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                f"El tramo tiene que estar dentro del audio y durar "
                f"{CONFIG.escucha_max_segundos:g} s como máximo",
            )
        return Response(recortar(analisis.wav, inicio, fin), media_type="audio/wav")

    return app


app = crear_app()
