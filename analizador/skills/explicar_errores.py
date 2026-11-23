"""Skill explicar_errores: explica los problemas encontrados y cómo corregirlos.

Usa Claude si el agente tiene configuración "llm" y hay un cliente disponible.
Si no, o si la llamada falla, genera la explicación con reglas fijas
(config/sugerencias.json). Así el programa nunca depende de la IA para
funcionar, y la IA nunca decide qué es un error: solo explica lo que ya
detectaron las skills de validación.
"""

from collections import OrderedDict

from . import skill
from ..llm import ErrorLLM


def agrupar_problemas(reporte):
    """Agrupa los números de línea por tipo de problema, en orden de aparición."""
    grupos = OrderedDict()
    for linea in reporte.con_problemas:
        for p in linea.problemas:
            grupos.setdefault(p.codigo, []).append(linea.numero)
    return grupos


def lineas_conteo(grupos, sugerencias):
    """'- Correo inválido: 5 (líneas 16, 17, 18, 20, 22)' por cada tipo."""
    salida = []
    for codigo, numeros in grupos.items():
        titulo = sugerencias.get(codigo, {}).get("titulo", codigo)
        etiqueta = "línea" if len(numeros) == 1 else "líneas"
        salida.append(f"- {titulo}: {len(numeros)} ({etiqueta} {', '.join(map(str, numeros))})")
    return salida


def construir_mensaje(reporte, max_lineas, sugerencias):
    """Arma el mensaje para el modelo: resumen, conteo por tipo y líneas con problemas.

    El conteo por tipo lo calcula el programa y se envía ya hecho. Al probar
    con la API real, Claude contó mal (dijo 6 correos inválidos cuando eran 5),
    así que los números salen del código y la IA solo los redacta.
    """
    tipos = ", ".join(f"{k}: {v}" for k, v in reporte.por_tipo.items())
    partes = [
        f"Archivo: {reporte.archivo}",
        f"Total de eventos: {reporte.total_eventos}",
        f"Eventos por tipo: {tipos}",
        f"Líneas mal formateadas: {reporte.mal_formateadas}",
        "",
        "Conteo de problemas por tipo (calculado por el validador; usa estos números tal cual):",
        *lineas_conteo(agrupar_problemas(reporte), sugerencias),
        "",
        "Líneas con problemas:",
    ]
    con_problemas = reporte.con_problemas
    for linea in con_problemas[:max_lineas]:
        motivos = "; ".join(p.mensaje for p in linea.problemas)
        partes.append(f"- Línea {linea.numero}: {linea.texto.strip()}  ->  {motivos}")
    omitidas = len(con_problemas) - max_lineas
    if omitidas > 0:
        # Se avisa explícitamente al modelo; no se recorta en silencio.
        partes.append(f"(Hay {omitidas} líneas más con problemas que no se incluyen aquí.)")
    return "\n".join(partes)


def explicacion_por_reglas(reporte, sugerencias):
    """Explicación sin IA: agrupa los problemas por tipo con su sugerencia."""
    grupos = agrupar_problemas(reporte)

    mas_frecuente = max(grupos, key=lambda c: len(grupos[c]))
    titulo = lambda c: sugerencias.get(c, {}).get("titulo", c)
    texto = [
        f"{reporte.mal_formateadas} de {reporte.total_eventos} eventos tienen problemas. "
        f"El más frecuente es \"{titulo(mas_frecuente)}\" ({len(grupos[mas_frecuente])} líneas).",
        "",
    ]
    for codigo, linea_conteo in zip(grupos, lineas_conteo(grupos, sugerencias)):
        texto.append(linea_conteo)
        sugerencia = sugerencias.get(codigo, {}).get("sugerencia")
        if sugerencia:
            texto.append(f"  Cómo corregirlo: {sugerencia}")
    return "\n".join(texto)


@skill("explicar_errores", "reporte", "Explica los problemas y sugiere correcciones; usa Claude si está disponible.")
def explicar_errores(reporte, entorno):
    if not reporte.con_problemas:
        reporte.explicacion = "No hay líneas con problemas. El archivo está bien formado."
        reporte.explicacion_fuente = "reglas"
        return

    config_llm = entorno.definicion.llm
    motivo = entorno.motivo_sin_ia
    if config_llm and entorno.llm:
        try:
            mensaje = construir_mensaje(reporte, config_llm.max_lineas_contexto, entorno.sugerencias)
            texto, modelo = entorno.llm.completar(config_llm, mensaje)
            reporte.explicacion = texto
            reporte.explicacion_fuente = f"IA ({modelo})"
            return
        except ErrorLLM as e:
            motivo = str(e)
    elif not config_llm:
        motivo = "este agente no tiene configuración de IA"

    reporte.explicacion = explicacion_por_reglas(reporte, entorno.sugerencias)
    reporte.explicacion_fuente = f"reglas, sin IA: {motivo}" if motivo else "reglas"
