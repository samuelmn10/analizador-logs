"""
Punto de entrada del analizador de logs con agentes.

Uso:
    python3 main.py pruebas/logs_malos.txt                      -> agente validador
    python3 main.py pruebas/logs_malos.txt --agente analista    -> explica con IA
    python3 main.py pruebas/logs_malos.txt -a analista --sin-ia -> explica sin IA
    python3 main.py --listar                                    -> agentes y skills
"""

import argparse
import sys
from pathlib import Path

from analizador import skills
from analizador.agente import crear_agente
from analizador.config import CARPETA_CONFIG, ErrorConfiguracion, cargar_agentes, cargar_env
from analizador.llm import ClienteClaude, ErrorLLM
from analizador.salida import mostrar_reporte


def listar(carpeta):
    print("AGENTES (config/agentes.json)")
    for nombre, d in cargar_agentes(carpeta).items():
        ia = " [usa IA]" if d.llm else ""
        print(f"  {nombre}{ia}: {d.descripcion}")
        print(f"      skills: {', '.join(d.skills_linea + d.skills_reporte)}")
    print("\nSKILLS DISPONIBLES (analizador/skills/)")
    for s in skills.REGISTRO.values():
        print(f"  {s.nombre} ({s.tipo}): {s.descripcion}")


def preparar_llm(definicion_tiene_llm, sin_ia):
    """Crea el cliente de Claude solo si el agente lo necesita."""
    if not definicion_tiene_llm:
        return None, ""
    if sin_ia:
        return None, "desactivada con --sin-ia"
    cargar_env()  # lee ANTHROPIC_API_KEY desde .env, si existe
    try:
        return ClienteClaude(), ""
    except ErrorLLM as e:
        return None, str(e)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Analiza un archivo de logs con un agente configurable.")
    parser.add_argument("archivo", nargs="?", help="ruta del archivo de logs")
    parser.add_argument("-a", "--agente", default="validador", help="agente a usar (por defecto: validador)")
    parser.add_argument("--sin-ia", action="store_true", help="no llamar al modelo aunque el agente use IA")
    parser.add_argument("--listar", action="store_true", help="muestra los agentes y skills disponibles")
    parser.add_argument("--config", default=str(CARPETA_CONFIG), help="carpeta de configuración")
    args = parser.parse_args(argv)

    try:
        if args.listar:
            listar(args.config)
            return 0

        ruta = Path(args.archivo or input("Ruta del archivo de logs a analizar: ").strip().strip('"'))
        if not str(ruta) or str(ruta) == ".":
            print("Error: no se indicó ningún archivo.")
            return 1
        if not ruta.exists():
            print(f"Error: el archivo '{ruta}' no existe.")
            return 1
        if not ruta.is_file():
            print(f"Error: '{ruta}' no es un archivo.")
            return 1

        definicion = cargar_agentes(args.config).get(args.agente)
        llm, motivo = preparar_llm(bool(definicion and definicion.llm), args.sin_ia)
        agente = crear_agente(args.agente, args.config, llm=llm, motivo_sin_ia=motivo)
        reporte = agente.analizar_archivo(ruta)
        mostrar_reporte(reporte, agente.definicion)
        return 0
    except ErrorConfiguracion as e:
        print(f"Error de configuración: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
