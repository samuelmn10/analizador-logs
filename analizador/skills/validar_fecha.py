"""Skill validar_fecha: comprueba que la fecha exista y tenga el formato correcto."""

from datetime import datetime

from . import skill


def es_fecha_valida(texto, formato):
    """True si el texto es una fecha real (rechaza 2025-13-45 o 2025-02-30)."""
    try:
        datetime.strptime(texto, formato)
        return True
    except ValueError:
        return False


@skill("validar_fecha", "linea", "Marca fechas inexistentes o en otro formato, y la falta de fecha.")
def validar_fecha(ctx, entorno):
    if not ctx.tiene_corchetes:
        return  # sin estructura no tiene sentido buscar la fecha
    if ctx.fecha_texto:
        if es_fecha_valida(ctx.fecha_texto, entorno.reglas.formato_fecha):
            ctx.fecha = "valida"
        else:
            ctx.fecha = "invalida"
            ctx.agregar("fecha_invalida", f"fecha inválida: {ctx.fecha_texto}")
    elif entorno.reglas.sin_fecha_es_incompleta:
        ctx.agregar("falta_fecha", "falta la fecha")
