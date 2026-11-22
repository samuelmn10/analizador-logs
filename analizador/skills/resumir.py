"""Skill resumir: calcula los totales del reporte."""

from . import skill


@skill("resumir", "reporte", "Cuenta los eventos, los eventos por tipo y las líneas mal formateadas.")
def resumir(reporte, entorno):
    reporte.total_eventos = len(reporte.lineas)
    reporte.por_tipo = {nivel: 0 for nivel in entorno.reglas.niveles_validos}
    for linea in reporte.lineas:
        # Un evento con nivel reconocido cuenta en su tipo aunque tenga otros
        # problemas (ej. falta la fecha): el tipo sí se conoce.
        if linea.nivel:
            reporte.por_tipo[linea.nivel] += 1
    reporte.mal_formateadas = len(reporte.con_problemas)
