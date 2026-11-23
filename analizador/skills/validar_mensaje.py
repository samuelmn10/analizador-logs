"""Skill validar_mensaje: exige que el evento tenga un mensaje."""

from . import skill


@skill("validar_mensaje", "linea", "Marca las líneas sin mensaje (ej. '[INFO] 2025-01-10').")
def validar_mensaje(ctx, entorno):
    if ctx.tiene_corchetes and entorno.reglas.mensaje_obligatorio and not ctx.mensaje:
        ctx.agregar("falta_mensaje", "falta el mensaje")
