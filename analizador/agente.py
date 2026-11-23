"""
Agente: ejecuta una lista de skills definida en config/agentes.json.

Todos los agentes usan esta misma clase. Lo que cambia entre uno y otro
(qué skills usa, si muestra el detalle, si usa IA y con qué prompt) está
en la configuración, no en el código.
"""

from dataclasses import dataclass
from pathlib import Path

from . import skills as registro_skills
from .config import (
    CARPETA_CONFIG, ErrorConfiguracion, cargar_agentes, cargar_reglas, cargar_sugerencias,
)
from .modelos import LineaContexto, Reporte


@dataclass
class Entorno:
    """Lo que una skill puede consultar, además de la línea o el reporte."""
    reglas: object
    sugerencias: dict
    definicion: object
    llm: object = None           # ClienteClaude u otro objeto con .completar()
    motivo_sin_ia: str = ""      # por qué no hay cliente de IA, si no lo hay


class Agente:
    def __init__(self, definicion, reglas, sugerencias, llm=None, motivo_sin_ia=""):
        if not definicion.skills_linea or definicion.skills_linea[0] != "parsear_linea":
            # Las demás skills de línea leen lo que extrae parsear_linea.
            raise ErrorConfiguracion(
                f"El agente '{definicion.nombre}' debe tener 'parsear_linea' como primera skill de línea"
            )
        self.definicion = definicion
        self.entorno = Entorno(reglas, sugerencias, definicion, llm, motivo_sin_ia)
        self._skills_linea = [registro_skills.obtener(n, "linea") for n in definicion.skills_linea]
        self._skills_reporte = [registro_skills.obtener(n, "reporte") for n in definicion.skills_reporte]

    @property
    def nombre(self):
        return self.definicion.nombre

    def analizar_linea(self, numero, texto):
        """Procesa una línea. Devuelve None si es una línea vacía ignorada."""
        ctx = LineaContexto(numero=numero, texto=texto.rstrip("\n"))
        parsear, *validaciones = self._skills_linea
        parsear.funcion(ctx, self.entorno)

        if ctx.vacia:
            if self.entorno.reglas.ignorar_lineas_vacias:
                return None
            ctx.agregar("linea_vacia", "línea vacía")
            return ctx

        for s in validaciones:
            s.funcion(ctx, self.entorno)
        return ctx

    def analizar_archivo(self, ruta):
        reporte = Reporte(archivo=str(ruta), agente=self.nombre)
        # errors="replace": un carácter con otra codificación no detiene el programa.
        with open(ruta, encoding="utf-8", errors="replace") as archivo:
            for numero, texto in enumerate(archivo, start=1):
                ctx = self.analizar_linea(numero, texto)
                if ctx is not None:
                    reporte.lineas.append(ctx)
        for s in self._skills_reporte:
            s.funcion(reporte, self.entorno)
        return reporte


def crear_agente(nombre, carpeta_config=CARPETA_CONFIG, llm=None, motivo_sin_ia=""):
    """Arma un agente a partir de su nombre en config/agentes.json."""
    carpeta = Path(carpeta_config)
    agentes = cargar_agentes(carpeta)
    if nombre not in agentes:
        raise ErrorConfiguracion(
            f"No existe el agente '{nombre}'. Disponibles: {', '.join(agentes)}"
        )
    return Agente(agentes[nombre], cargar_reglas(carpeta), cargar_sugerencias(carpeta), llm, motivo_sin_ia)
