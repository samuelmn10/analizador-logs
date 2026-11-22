"""
Analizador de logs con skills y agentes personalizables.

Estructura:
    config.py   -> carga reglas, agentes y sugerencias desde config/ (JSON).
    modelos.py  -> estructuras de datos compartidas (línea, problema, reporte).
    skills/     -> capacidades pequeñas y reutilizables (una por archivo).
    agente.py   -> un agente ejecuta una lista de skills definida en config/agentes.json.
    llm.py      -> cliente opcional de Claude para la skill explicar_errores.
    salida.py   -> muestra el reporte en consola.
"""
