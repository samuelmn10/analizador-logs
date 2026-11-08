"""
Analizador de archivos de logs.

Lee un archivo de texto donde cada línea es un evento con el formato esperado:

    [NIVEL] AAAA-MM-DD mensaje

y genera un resumen en consola: total de eventos, cantidad por tipo
y número de líneas mal formateadas o incompletas.

Uso:
    python analizador_logs.py                     -> pide la ruta del archivo
    python analizador_logs.py pruebas/logs_buenos.txt
"""

import re
import sys
from datetime import datetime
from pathlib import Path


# =============================================================================
# REGLAS DE VALIDACIÓN  (DECISIONES DEL ESTUDIANTE)
# -----------------------------------------------------------------------------
# Esta es la parte que el enunciado pide que decidas TÚ, no la IA.
# Los valores de abajo son una PROPUESTA inicial para que el programa funcione.
# Revisa cada una, cámbiala si no estás de acuerdo y justifícala en
# REFLEXION.md. Cada decisión está aislada en una constante para que cambiar
# de opinión no obligue a tocar la lógica del programa.
# =============================================================================

# Niveles de severidad que se consideran válidos.
NIVELES_VALIDOS = ("INFO", "WARNING", "ERROR")

# ¿Se acepta "[info]" o "[Error]" como válido?
#   True  -> se normaliza a mayúsculas y se cuenta normalmente.
#   False -> se marca como línea mal formateada.
ACEPTAR_NIVEL_EN_MINUSCULAS = True

# Formato de fecha aceptado (el del enunciado: 2025-01-10).
# Se valida con datetime, así que fechas imposibles como 2025-13-45 o
# 2025-02-30 se rechazan, no solo se revisa que "parezcan" fechas.
FORMATO_FECHA = "%Y-%m-%d"

# ¿Una línea SIN fecha cuenta como mal formateada/incompleta?
#   True  -> sí (el evento se cuenta en su tipo, pero también como incompleto).
#   False -> se acepta como válida aunque no tenga fecha.
SIN_FECHA_ES_INCOMPLETA = True

# ¿Una línea sin mensaje (ej: "[INFO] 2025-01-10") es incompleta?
MENSAJE_OBLIGATORIO = True

# ¿Qué hacer con las líneas vacías o solo con espacios?
#   True  -> se ignoran: no son eventos ni errores.
#   False -> se cuentan como líneas mal formateadas.
IGNORAR_LINEAS_VACIAS = True

# --- Nombres propios -------------------------------------------------------
# El nombre se busca SOLO en el campo "usuario=" del mensaje, por ejemplo:
#     [INFO] 2025-01-10 Login usuario=Juan Pérez correo=juan@gmail.com
# Se decidió usar un campo marcado porque en el mensaje hay otras palabras
# con mayúscula ("Login", "User") que NO son nombres propios.
# El nombre termina donde empieza el siguiente campo (ej: "correo=") o al
# final de la línea.
CAMPO_NOMBRE = "usuario"

# Cada palabra del nombre debe empezar con mayúscula: "Juan Pérez" sí,
# "juan pérez" no.
NOMBRE_MAYUSCULA_INICIAL = True

# ¿Se aceptan tildes y ñ? ("Pérez", "Muñoz", "José")
NOMBRE_ACEPTA_TILDES_Y_ENIE = True

# Exige al menos dos palabras (nombre y apellido): "Juan" solo no es válido.
NOMBRE_MINIMO_DOS_PALABRAS = True

# Solo se permiten letras: "Juan3 Pérez" o "Juan_P" son inválidos porque un
# nombre propio real no lleva números ni símbolos.
NOMBRE_SOLO_LETRAS = True

# --- Correos electrónicos -------------------------------------------------
# El correo se busca en el campo "correo=" del mensaje y debe tener tres
# partes:  identificador  @  servicio.dominio
#          juan.perez     @  gmail.com
# Un correo mal escrito hace que la línea cuente como MAL FORMATEADA
# (igual que una fecha inválida), pero el evento sigue contando en su tipo.
CAMPO_CORREO = "correo"


# =============================================================================
# EXPRESIONES REGULARES  (aquí la IA sí puede ayudar a proponerlas)
# =============================================================================

# Captura "[ALGO]" al inicio de la línea y el resto del texto.
# Se acepta cualquier palabra entre corchetes para poder REPORTAR niveles
# desconocidos (ej: [DEBUG]) en vez de simplemente no reconocer la línea.
PATRON_LINEA = re.compile(r"^\[(?P<nivel>[^\]]*)\]\s*(?P<resto>.*)$")

# Detecta si el primer "token" del resto PARECE una fecha (solo dígitos y
# separadores). OJO: esto solo decide si hay un intento de fecha; si es una
# fecha VÁLIDA lo decide datetime.strptime más abajo. Una regex como
# \d{4}-\d{2}-\d{2} por sí sola aceptaría 2025-13-45.
PATRON_POSIBLE_FECHA = re.compile(r"^[\d][\d\-/.]*$")

# Captura el valor del campo usuario=: todo lo que sigue hasta el próximo
# "palabra=" (otro campo) o hasta el final de la línea.
#   "Login usuario=Juan Pérez correo=juan@gmail.com"  ->  "Juan Pérez"
PATRON_CAMPO_NOMBRE = re.compile(
    rf"\b{CAMPO_NOMBRE}=(?P<valor>.*?)(?=\s+\w+=|$)"
)

# Captura el valor del campo correo=: hasta el primer espacio, porque un
# correo nunca lleva espacios.
PATRON_CAMPO_CORREO = re.compile(rf"\b{CAMPO_CORREO}=(?P<valor>\S*)")

# Formato del correo, por partes:
#   [A-Za-z0-9._%+-]+        identificador: letras, números y . _ % + -
#   @                         exactamente una arroba
#   [A-Za-z0-9-]+             servicio: gmail, hotmail, empresa...
#   (\.[A-Za-z0-9-]+)*        subdominios opcionales: .com en "empresa.com.sv"
#   \.[A-Za-z]{2,}            dominio final de 2 o más letras: .com, .sv, .org
PATRON_CORREO = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$"
)

# Letras con y sin tilde, usadas para validar nombres.
MAYUSCULAS_CON_TILDE = "ÁÉÍÓÚÜÑ"
MINUSCULAS_CON_TILDE = "áéíóúüñ"


# =============================================================================
# LÓGICA DE ANÁLISIS
# =============================================================================

def validar_fecha(texto):
    """Devuelve True si el texto es una fecha real en FORMATO_FECHA."""
    try:
        datetime.strptime(texto, FORMATO_FECHA)
        return True
    except ValueError:
        return False


def validar_nombre(nombre):
    """
    Revisa un nombre propio según las reglas NOMBRE_* de arriba.
    Devuelve una lista de motivos por los que es inválido (vacía si es válido).
    """
    if not nombre:
        return ["está vacío"]

    motivos = []
    palabras = nombre.split()

    if NOMBRE_MINIMO_DOS_PALABRAS and len(palabras) < 2:
        motivos.append("debe tener nombre y apellido")

    mayusculas = "A-Z" + (MAYUSCULAS_CON_TILDE if NOMBRE_ACEPTA_TILDES_Y_ENIE else "")
    letras = mayusculas + "a-z" + (MINUSCULAS_CON_TILDE if NOMBRE_ACEPTA_TILDES_Y_ENIE else "")

    for palabra in palabras:
        if NOMBRE_MAYUSCULA_INICIAL and not re.match(f"[{mayusculas}]", palabra):
            motivo = "cada palabra debe empezar con mayúscula"
            if motivo not in motivos:
                motivos.append(motivo)
        if NOMBRE_SOLO_LETRAS and not re.fullmatch(f"[{letras}]+", palabra):
            motivo = "solo puede tener letras"
            if motivo not in motivos:
                motivos.append(motivo)
        if not NOMBRE_ACEPTA_TILDES_Y_ENIE and any(
            letra in MAYUSCULAS_CON_TILDE + MINUSCULAS_CON_TILDE for letra in palabra
        ):
            motivo = "no se aceptan tildes ni ñ"
            if motivo not in motivos:
                motivos.append(motivo)

    return motivos


def validar_correo(correo):
    """
    Revisa un correo y devuelve el motivo si es inválido, o None si es válido.
    Se dan motivos específicos (no solo "inválido") para que quien lea el
    resumen sepa qué corregir.
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
    if ".." in correo:
        return "tiene dos puntos seguidos"
    if identificador.startswith(".") or identificador.endswith("."):
        return "el identificador no puede empezar ni terminar con punto"
    if "." not in servicio:
        return "el servicio no tiene dominio (ej: .com)"
    if not PATRON_CORREO.match(correo):
        return "tiene caracteres no permitidos o un dominio inválido"
    return None


def revisar_campos(mensaje):
    """
    Busca los campos usuario= y correo= dentro del mensaje y los valida.
    Devuelve la lista de problemas encontrados (vacía si todo está bien).
    Si el mensaje no trae esos campos, no es un problema: no todos los
    eventos involucran a un usuario.
    """
    problemas = []

    for coincidencia in PATRON_CAMPO_NOMBRE.finditer(mensaje):
        nombre = coincidencia.group("valor").strip()
        motivos = validar_nombre(nombre)
        if motivos:
            problemas.append(f'nombre inválido "{nombre}": {", ".join(motivos)}')

    for coincidencia in PATRON_CAMPO_CORREO.finditer(mensaje):
        correo = coincidencia.group("valor")
        motivo = validar_correo(correo)
        if motivo:
            problemas.append(f'correo inválido "{correo}": {motivo}')

    return problemas


def analizar_linea(linea):
    """
    Analiza una línea y devuelve un diccionario con:
        nivel     -> "INFO" / "WARNING" / "ERROR" o None si no es válido
        fecha     -> "valida", "invalida" o "ausente"
        mensaje   -> texto del mensaje (puede ser "")
        problemas -> lista de textos que explican por qué la línea falla
    Si la línea está vacía y se decidió ignorarlas, devuelve None.
    """
    contenido = linea.strip()

    if not contenido:
        if IGNORAR_LINEAS_VACIAS:
            return None
        return {"nivel": None, "fecha": "ausente", "mensaje": "",
                "problemas": ["línea vacía"]}

    resultado = {"nivel": None, "fecha": "ausente", "mensaje": "",
                 "problemas": []}

    coincidencia = PATRON_LINEA.match(contenido)
    if not coincidencia:
        # Sin "[NIVEL]" al inicio no se puede saber qué tipo de evento es.
        resultado["problemas"].append("no tiene nivel entre corchetes")
        return resultado

    # --- Nivel ---
    nivel_original = coincidencia.group("nivel").strip()
    nivel = nivel_original.upper() if ACEPTAR_NIVEL_EN_MINUSCULAS else nivel_original
    if nivel in NIVELES_VALIDOS:
        resultado["nivel"] = nivel
    elif nivel_original == "":
        resultado["problemas"].append("nivel vacío: []")
    else:
        resultado["problemas"].append(f"nivel desconocido: [{nivel_original}]")

    # --- Fecha y mensaje ---
    resto = coincidencia.group("resto").strip()
    partes = resto.split(maxsplit=1)
    primer_token = partes[0] if partes else ""

    if primer_token and PATRON_POSIBLE_FECHA.match(primer_token):
        # Hay algo que intenta ser fecha: se valida de verdad.
        resultado["mensaje"] = partes[1] if len(partes) > 1 else ""
        if validar_fecha(primer_token):
            resultado["fecha"] = "valida"
        else:
            resultado["fecha"] = "invalida"
            resultado["problemas"].append(f"fecha inválida: {primer_token}")
    else:
        # No hay fecha: todo el resto es el mensaje.
        resultado["mensaje"] = resto
        if SIN_FECHA_ES_INCOMPLETA:
            resultado["problemas"].append("falta la fecha")

    if MENSAJE_OBLIGATORIO and not resultado["mensaje"]:
        resultado["problemas"].append("falta el mensaje")

    # --- Nombres y correos dentro del mensaje ---
    resultado["problemas"].extend(revisar_campos(resultado["mensaje"]))

    return resultado


def analizar_archivo(ruta):
    """
    Recorre el archivo línea por línea y acumula los conteos.
    Se lee línea a línea (no todo de golpe) para soportar archivos grandes.
    """
    resumen = {
        "total_eventos": 0,
        "por_tipo": {nivel: 0 for nivel in NIVELES_VALIDOS},
        "mal_formateadas": 0,
        "detalle_errores": [],   # (número de línea, texto, problemas)
    }

    # errors="replace": si el archivo trae caracteres raros (otra codificación)
    # no se cae el programa; esos caracteres se muestran como "?".
    with open(ruta, encoding="utf-8", errors="replace") as archivo:
        for numero, linea in enumerate(archivo, start=1):
            resultado = analizar_linea(linea)
            if resultado is None:
                continue  # línea vacía ignorada

            resumen["total_eventos"] += 1

            # Un evento con nivel reconocido se cuenta en su tipo AUNQUE le
            # falte la fecha: el tipo sí se conoce. Además se cuenta como
            # mal formateado si tiene problemas.
            if resultado["nivel"]:
                resumen["por_tipo"][resultado["nivel"]] += 1

            if resultado["problemas"]:
                resumen["mal_formateadas"] += 1
                resumen["detalle_errores"].append(
                    (numero, linea.rstrip("\n"), resultado["problemas"])
                )

    return resumen


# =============================================================================
# ENTRADA / SALIDA
# =============================================================================

def pedir_ruta():
    """Obtiene la ruta del archivo: desde la línea de comandos o preguntando."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    return input("Ruta del archivo de logs a analizar: ").strip().strip('"')


def mostrar_resumen(ruta, resumen):
    """Imprime el resultado de forma clara en consola."""
    linea = "=" * 50
    print(linea)
    print(f" RESUMEN DE LOGS: {ruta}")
    print(linea)
    print(f" Total de eventos:           {resumen['total_eventos']}")
    for nivel, cantidad in resumen["por_tipo"].items():
        print(f"   - {nivel:<10}               {cantidad}")
    sin_tipo = resumen["total_eventos"] - sum(resumen["por_tipo"].values())
    print(f"   - Sin tipo válido          {sin_tipo}")
    print(f" Líneas mal formateadas:     {resumen['mal_formateadas']}")
    print(linea)

    if resumen["detalle_errores"]:
        print(" DETALLE DE LÍNEAS CON PROBLEMAS")
        print(linea)
        for numero, texto, problemas in resumen["detalle_errores"]:
            print(f" Línea {numero}: {texto}")
            print(f"    -> {', '.join(problemas)}")
        print(linea)


def main():
    ruta = Path(pedir_ruta())

    # Validaciones del archivo ANTES de analizar, con mensajes claros
    # en vez de dejar que Python muestre un error técnico.
    if not str(ruta) or str(ruta) == ".":
        print("Error: no se indicó ningún archivo.")
        return 1
    if not ruta.exists():
        print(f"Error: el archivo '{ruta}' no existe.")
        return 1
    if not ruta.is_file():
        print(f"Error: '{ruta}' no es un archivo.")
        return 1

    resumen = analizar_archivo(ruta)

    if resumen["total_eventos"] == 0:
        print(f"El archivo '{ruta}' no contiene eventos.")
        return 0

    mostrar_resumen(ruta, resumen)
    return 0


if __name__ == "__main__":
    sys.exit(main())
