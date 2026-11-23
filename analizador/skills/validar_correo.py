"""Skill validar_correo: valida el formato del correo del campo correo=."""

import re
from functools import lru_cache

from . import skill

# identificador @ servicio . dominio (2+ letras); permite subdominios (.com.sv)
PATRON_CORREO = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$"
)


@lru_cache(maxsize=None)
def _patron_campo(campo):
    # Un correo nunca lleva espacios: el valor termina en el primer espacio.
    return re.compile(rf"\b{re.escape(campo)}=(?P<valor>\S*)")


def motivo_correo(correo):
    """Devuelve el motivo por el que el correo es inválido, o None si es válido.

    Las revisiones van de la más general a la más específica para que el
    mensaje diga exactamente qué corregir.
    """
    if not correo:
        return "está vacío"
    if correo.count("@") == 0:
        return "falta la @"
    if correo.count("@") > 1:
        return "tiene más de una @"
    identificador, servicio = correo.split("@")
    if not identificador:
        return "falta el identificador antes de la @"
    if not servicio:
        return "falta el servicio después de la @"
    # Agregado en la Semana 3: la regex de la IA aceptaba estos casos.
    if ".." in correo:
        return "tiene dos puntos seguidos"
    if identificador.startswith(".") or identificador.endswith("."):
        return "el identificador no puede empezar ni terminar con punto"
    if "." not in servicio:
        return "el servicio no tiene dominio (ej: .com)"
    if not PATRON_CORREO.match(correo):
        return "tiene caracteres no permitidos o un dominio inválido"
    return None


@skill("validar_correo", "linea", "Valida el formato identificador@servicio.dominio del campo correo=.")
def validar_correo(ctx, entorno):
    if not ctx.tiene_corchetes:
        return
    for m in _patron_campo(entorno.reglas.correo.campo).finditer(ctx.mensaje):
        correo = m.group("valor")
        motivo = motivo_correo(correo)
        if motivo:
            ctx.agregar("correo_invalido", f'correo inválido "{correo}": {motivo}')
