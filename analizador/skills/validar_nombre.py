"""Skill validar_nombre: valida el nombre propio del campo usuario=."""

import re
from functools import lru_cache

from . import skill

MAYUSCULAS_CON_TILDE = "ÁÉÍÓÚÜÑ"
MINUSCULAS_CON_TILDE = "áéíóúüñ"


@lru_cache(maxsize=None)
def _patron_campo(campo):
    # El nombre termina donde empieza el siguiente "campo=" o al final.
    return re.compile(rf"\b{re.escape(campo)}=(?P<valor>.*?)(?=\s+\w+=|$)")


def motivos_nombre(nombre, reglas_nombre):
    """Devuelve la lista de motivos por los que el nombre es inválido."""
    if not nombre:
        return ["está vacío"]

    r = reglas_nombre
    motivos = []
    palabras = nombre.split()

    if r.minimo_dos_palabras and len(palabras) < 2:
        motivos.append("debe tener nombre y apellido")

    mayusculas = "A-Z" + (MAYUSCULAS_CON_TILDE if r.acepta_tildes_y_enie else "")
    letras = mayusculas + "a-z" + (MINUSCULAS_CON_TILDE if r.acepta_tildes_y_enie else "")

    def anotar(motivo):
        if motivo not in motivos:
            motivos.append(motivo)

    for palabra in palabras:
        if r.mayuscula_inicial and not re.match(f"[{mayusculas}]", palabra):
            anotar("cada palabra debe empezar con mayúscula")
        if r.solo_letras and not re.fullmatch(f"[{letras}]+", palabra):
            anotar("solo puede tener letras")
        if not r.acepta_tildes_y_enie and any(
            c in MAYUSCULAS_CON_TILDE + MINUSCULAS_CON_TILDE for c in palabra
        ):
            anotar("no se aceptan tildes ni ñ")
    return motivos


@skill("validar_nombre", "linea", "Valida el nombre propio del campo usuario= según las reglas de nombre.")
def validar_nombre(ctx, entorno):
    if not ctx.tiene_corchetes:
        return
    reglas_nombre = entorno.reglas.nombre
    for m in _patron_campo(reglas_nombre.campo).finditer(ctx.mensaje):
        nombre = m.group("valor").strip()
        motivos = motivos_nombre(nombre, reglas_nombre)
        if motivos:
            ctx.agregar("nombre_invalido", f'nombre inválido "{nombre}": {", ".join(motivos)}')
