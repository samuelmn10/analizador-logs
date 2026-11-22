"""Skill parsear_linea: separa una línea en nivel, fecha y mensaje.

Solo EXTRAE datos; no decide si son válidos. Esa separación es la clave
de la refactorización: antes, analizar_linea() extraía y validaba todo
junto, y no se podía reutilizar una parte sin la otra.
Debe ser la primera skill de línea de cualquier agente.
"""

import re

from . import skill

# "[ALGO] resto": se acepta cualquier texto entre corchetes para poder
# reportar niveles desconocidos (ej. [DEBUG]) en vez de ignorarlos.
PATRON_LINEA = re.compile(r"^\[(?P<nivel>[^\]]*)\]\s*(?P<resto>.*)$")

# El primer token "parece fecha" si empieza con dígito y solo tiene dígitos
# y separadores. Si es una fecha REAL lo decide la skill validar_fecha.
PATRON_POSIBLE_FECHA = re.compile(r"^[\d][\d\-/.]*$")


@skill("parsear_linea", "linea", "Separa la línea en nivel, fecha y mensaje, sin validarlos.")
def parsear_linea(ctx, entorno):
    contenido = ctx.texto.strip()
    if not contenido:
        ctx.vacia = True
        return

    coincidencia = PATRON_LINEA.match(contenido)
    if not coincidencia:
        return  # sin corchetes: validar_nivel lo reporta

    ctx.tiene_corchetes = True
    ctx.nivel_texto = coincidencia.group("nivel").strip()

    # Clasificar el nivel aquí (y no en validar_nivel) permite contar los
    # eventos por tipo aunque un agente no use la skill validar_nivel.
    reglas = entorno.reglas
    nivel = ctx.nivel_texto.upper() if reglas.aceptar_nivel_en_minusculas else ctx.nivel_texto
    if nivel in reglas.niveles_validos:
        ctx.nivel = nivel

    resto = coincidencia.group("resto").strip()
    partes = resto.split(maxsplit=1)
    primer_token = partes[0] if partes else ""
    if primer_token and PATRON_POSIBLE_FECHA.match(primer_token):
        ctx.fecha_texto = primer_token
        ctx.mensaje = partes[1] if len(partes) > 1 else ""
    else:
        ctx.mensaje = resto
