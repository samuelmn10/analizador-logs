"""
Registro de skills.

Una skill es una función pequeña que hace UNA cosa. Hay dos tipos:
    - "linea":   recibe (contexto_de_linea, entorno) y modifica el contexto.
    - "reporte": recibe (reporte, entorno) y modifica el reporte.

Cada skill se registra con el decorador @skill. Los agentes no importan
skills directamente: las piden por nombre desde config/agentes.json, así
que agregar una skill nueva es crear un archivo aquí y nombrarla en el JSON.
"""

from dataclasses import dataclass
from typing import Callable

from ..config import ErrorConfiguracion


@dataclass
class Skill:
    nombre: str
    tipo: str            # "linea" o "reporte"
    descripcion: str
    funcion: Callable


REGISTRO: dict[str, Skill] = {}


def skill(nombre: str, tipo: str, descripcion: str):
    """Decorador que registra una función como skill."""
    if tipo not in ("linea", "reporte"):
        raise ValueError(f"Tipo de skill inválido: {tipo}")

    def registrar(funcion):
        if nombre in REGISTRO:
            raise ValueError(f"Skill registrada dos veces: {nombre}")
        REGISTRO[nombre] = Skill(nombre, tipo, descripcion, funcion)
        return funcion
    return registrar


def obtener(nombre: str, tipo: str) -> Skill:
    """Busca una skill por nombre y comprueba que sea del tipo esperado."""
    if nombre not in REGISTRO:
        disponibles = ", ".join(sorted(REGISTRO))
        raise ErrorConfiguracion(f"Skill desconocida: '{nombre}'. Disponibles: {disponibles}")
    s = REGISTRO[nombre]
    if s.tipo != tipo:
        raise ErrorConfiguracion(f"La skill '{nombre}' es de tipo '{s.tipo}', no '{tipo}'")
    return s


# Importar los módulos para que se registren sus skills.
from . import (  # noqa: E402,F401
    parsear_linea, validar_nivel, validar_fecha, validar_mensaje,
    validar_nombre, validar_correo, resumir, explicar_errores,
)
