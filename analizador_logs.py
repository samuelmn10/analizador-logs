"""
Compatibilidad con la versión de la Semana 3.

Antes, todo el programa estaba en este archivo (reglas, expresiones
regulares, validaciones, lectura del archivo y salida en consola). Ahora
la lógica vive en el paquete analizador/ y este archivo solo traduce los
resultados al formato antiguo, para que:
    - el comando `python3 analizador_logs.py <archivo>` siga funcionando, y
    - las pruebas de la Semana 3 (tests/test_semana3.py) sigan pasando sin
      cambios, demostrando que la refactorización no cambió el comportamiento.
"""

import sys
from functools import lru_cache

from analizador.agente import crear_agente


@lru_cache(maxsize=None)
def _validador():
    return crear_agente("validador")


def analizar_linea(linea):
    """Formato antiguo: dict con nivel, fecha, mensaje y problemas (textos)."""
    ctx = _validador().analizar_linea(0, linea)
    if ctx is None:
        return None
    return {
        "nivel": ctx.nivel,
        "fecha": ctx.fecha,
        "mensaje": ctx.mensaje,
        "problemas": [p.mensaje for p in ctx.problemas],
    }


def analizar_archivo(ruta):
    """Formato antiguo: totales y lista (número, texto, problemas)."""
    reporte = _validador().analizar_archivo(ruta)
    return {
        "total_eventos": reporte.total_eventos,
        "por_tipo": reporte.por_tipo,
        "mal_formateadas": reporte.mal_formateadas,
        "detalle_errores": [
            (l.numero, l.texto, [p.mensaje for p in l.problemas]) for l in reporte.con_problemas
        ],
    }


if __name__ == "__main__":
    import main
    sys.exit(main.main(sys.argv[1:]))
