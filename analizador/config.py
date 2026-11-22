"""
Carga la configuración desde la carpeta config/.

Las reglas de validación y la definición de los agentes viven en archivos
JSON, no en el código. Para cambiar una regla o crear un agente nuevo no
hace falta tocar Python.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

CARPETA_CONFIG = Path(__file__).resolve().parent.parent / "config"


class ErrorConfiguracion(Exception):
    """La configuración tiene un error que impide ejecutar el agente."""


@dataclass
class ReglasNombre:
    campo: str = "usuario"
    mayuscula_inicial: bool = True
    acepta_tildes_y_enie: bool = True
    minimo_dos_palabras: bool = True
    solo_letras: bool = True


@dataclass
class ReglasCorreo:
    campo: str = "correo"


@dataclass
class Reglas:
    niveles_validos: tuple[str, ...] = ("INFO", "WARNING", "ERROR")
    aceptar_nivel_en_minusculas: bool = True
    formato_fecha: str = "%Y-%m-%d"
    sin_fecha_es_incompleta: bool = True
    mensaje_obligatorio: bool = True
    ignorar_lineas_vacias: bool = True
    nombre: ReglasNombre = field(default_factory=ReglasNombre)
    correo: ReglasCorreo = field(default_factory=ReglasCorreo)


@dataclass
class ConfigLLM:
    modelo: str
    max_tokens: int = 16000
    esfuerzo: str = "medium"
    max_lineas_contexto: int = 50
    prompt: str = ""        # texto del prompt de sistema (ya leído del archivo)


@dataclass
class DefinicionAgente:
    nombre: str
    descripcion: str
    skills_linea: list[str]
    skills_reporte: list[str]
    mostrar_detalle: bool = True
    llm: ConfigLLM | None = None


def _leer_json(ruta: Path) -> dict:
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise ErrorConfiguracion(f"No existe el archivo de configuración: {ruta}")
    except json.JSONDecodeError as e:
        raise ErrorConfiguracion(f"JSON inválido en {ruta}: {e}")


def cargar_reglas(carpeta: Path = CARPETA_CONFIG) -> Reglas:
    datos = _leer_json(Path(carpeta) / "reglas.json")
    try:
        return Reglas(
            niveles_validos=tuple(datos.get("niveles_validos", Reglas.niveles_validos)),
            aceptar_nivel_en_minusculas=datos.get("aceptar_nivel_en_minusculas", True),
            formato_fecha=datos.get("formato_fecha", "%Y-%m-%d"),
            sin_fecha_es_incompleta=datos.get("sin_fecha_es_incompleta", True),
            mensaje_obligatorio=datos.get("mensaje_obligatorio", True),
            ignorar_lineas_vacias=datos.get("ignorar_lineas_vacias", True),
            nombre=ReglasNombre(**datos.get("nombre", {})),
            correo=ReglasCorreo(**datos.get("correo", {})),
        )
    except TypeError as e:
        # Una clave desconocida en "nombre" o "correo" (por ejemplo un typo).
        raise ErrorConfiguracion(f"Clave desconocida en reglas.json: {e}")


def cargar_agentes(carpeta: Path = CARPETA_CONFIG) -> dict[str, DefinicionAgente]:
    carpeta = Path(carpeta)
    datos = _leer_json(carpeta / "agentes.json")
    agentes = {}
    for nombre, d in datos.items():
        llm = None
        if "llm" in d:
            ruta_prompt = carpeta / d["llm"].get("prompt", "")
            if not ruta_prompt.is_file():
                raise ErrorConfiguracion(f"El agente '{nombre}' apunta a un prompt que no existe: {ruta_prompt}")
            llm = ConfigLLM(
                modelo=d["llm"]["modelo"],
                max_tokens=d["llm"].get("max_tokens", 16000),
                esfuerzo=d["llm"].get("esfuerzo", "medium"),
                max_lineas_contexto=d["llm"].get("max_lineas_contexto", 50),
                prompt=ruta_prompt.read_text(encoding="utf-8"),
            )
        agentes[nombre] = DefinicionAgente(
            nombre=nombre,
            descripcion=d.get("descripcion", ""),
            skills_linea=d.get("skills_linea", []),
            skills_reporte=d.get("skills_reporte", []),
            mostrar_detalle=d.get("mostrar_detalle", True),
            llm=llm,
        )
    return agentes


def cargar_sugerencias(carpeta: Path = CARPETA_CONFIG) -> dict[str, str]:
    return _leer_json(Path(carpeta) / "sugerencias.json")
