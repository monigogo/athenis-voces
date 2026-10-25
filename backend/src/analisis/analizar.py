"""Junta todo el análisis en una sola función: EntradaAnalisis -> Resultado (Pasos.analizar).

Sustituye al falso del análisis. La entrada no trae el identificador del análisis: aquí se deja uno
provisional y el pipeline pone el de verdad.
"""

from analisis import indices, interrupciones, participacion, posicion
from config import CONFIG, Config
from contrato import EntradaAnalisis, EtiquetaVoz, MetricasGrupo, MetricasHablante, Resultado

SIN_IDENTIFICADOR = "pendiente"


def analizar(entrada: EntradaAnalisis, config: Config = CONFIG) -> Resultado:
    eventos = interrupciones.detectar(entrada, config)
    senales = [x for x in eventos if not x.tipo.cuenta_como_interrupcion]

    personas = participacion.por_hablante(entrada, senales, config)
    grupos = participacion.por_grupo(entrada, senales, config)
    presencia = participacion.presencia(entrada, senales, config)
    de_persona = {f.hablante: f for f in interrupciones.por_hablante(entrada, eventos, config)}
    de_grupo = {g.etiqueta: g for g in interrupciones.por_grupo(entrada, eventos, config)}
    abre = posicion.quien_abre(entrada, config)
    cierra = posicion.quien_cierra(entrada, config)
    ip = indices.protagonismo(
        segundos={f.hablante: f.segundos_habla for f in personas},
        abre=abre,
        cierra=cierra,
        turnos_largos={f.hablante: f.turnos_largos for f in personas},
        config=config,
    )
    tiempo = {g.etiqueta: g for g in grupos}
    fem, masc = tiempo[EtiquetaVoz.FEMENINO], tiempo[EtiquetaVoz.MASCULINO]

    return Resultado(
        id_analisis=SIN_IDENTIFICADOR,
        duracion=entrada.duracion,
        voz_femenina_presente=presencia.voz_femenina_presente,
        primera_intervencion_femenina=presencia.primera_intervencion_femenina,
        segundos_voces_cortas=presencia.segundos_voces_cortas,
        grupos=[
            MetricasGrupo(
                etiqueta=g.etiqueta,
                numero_voces=g.numero_voces,
                segundos_habla=g.segundos_habla,
                cuota_tiempo=g.cuota_tiempo,
                turnos=g.turnos,
                cuota_turnos=g.cuota_turnos,
                interrupciones_recibidas=de_grupo[g.etiqueta].recibidas,
                tasa_interrupcion_recibida=de_grupo[g.etiqueta].tasa_recibida,
            )
            for g in grupos
        ],
        hablantes=[
            MetricasHablante(
                hablante=f.hablante,
                etiqueta=f.etiqueta,
                origen=f.origen,
                segundos_habla=f.segundos_habla,
                turnos=f.turnos,
                turnos_largos=f.turnos_largos,
                abre=f.hablante == abre,
                cierra=f.hablante == cierra,
                interrupciones_recibidas=de_persona[f.hablante].recibidas,
                interrupciones_hechas=de_persona[f.hablante].hechas,
                tasa_interrupcion_recibida=de_persona[f.hablante].tasa_recibida,
                recupera_palabra=de_persona[f.hablante].recupera_palabra,
                apoyos_recibidos=de_persona[f.hablante].apoyos_recibidos,
                indice_protagonismo=ip[f.hablante],
            )
            for f in personas
        ],
        turnos=sorted(entrada.turnos, key=lambda t: (t.inicio, t.hablante)),
        solapamientos=entrada.solapamientos,
        interrupciones=eventos,
        indices=indices.de_grupo(
            t_f=fem.segundos_habla,
            t_m=masc.segundos_habla,
            n_f=fem.numero_voces,
            n_m=masc.numero_voces,
            i_f=de_grupo[EtiquetaVoz.FEMENINO].recibidas,
            i_m=de_grupo[EtiquetaVoz.MASCULINO].recibidas,
            config=config,
        ),
    )
