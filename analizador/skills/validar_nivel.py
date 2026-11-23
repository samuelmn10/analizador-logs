"""Skill validar_nivel: revisa que la línea tenga un nivel permitido."""

from . import skill


@skill("validar_nivel", "linea", "Reporta líneas sin corchetes, con nivel vacío o con nivel desconocido.")
def validar_nivel(ctx, entorno):
    if not ctx.tiene_corchetes:
        ctx.agregar("sin_corchetes", "no tiene nivel entre corchetes")
    elif ctx.nivel:
        return
    elif ctx.nivel_texto == "":
        ctx.agregar("nivel_vacio", "nivel vacío: []")
    else:
        ctx.agregar("nivel_desconocido", f"nivel desconocido: [{ctx.nivel_texto}]")
