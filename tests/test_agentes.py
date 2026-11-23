"""Pruebas de los agentes, la configuración y la skill que usa IA.

La IA se reemplaza por un cliente falso: las pruebas no llaman a la API,
no necesitan API key y no cuestan dinero.
"""

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import main
from analizador.agente import crear_agente
from analizador.config import CARPETA_CONFIG, ErrorConfiguracion
from analizador.llm import ErrorLLM

PRUEBAS = Path(__file__).resolve().parent.parent / "pruebas"
MALOS = PRUEBAS / "logs_malos.txt"
BUENOS = PRUEBAS / "logs_buenos.txt"


class LLMFalso:
    """Imita a ClienteClaude: guarda lo que recibe y devuelve un texto fijo."""

    def __init__(self, respuesta="Explicación de prueba", error=None):
        self.respuesta, self.error, self.mensajes = respuesta, error, []

    def completar(self, config, mensaje):
        self.mensajes.append(mensaje)
        if self.error:
            raise ErrorLLM(self.error)
        return self.respuesta, config.modelo


class TestAgentes(unittest.TestCase):

    def test_validador_igual_que_semana3(self):
        r = crear_agente("validador").analizar_archivo(MALOS)
        self.assertEqual(r.total_eventos, 21)
        self.assertEqual(r.por_tipo, {"INFO": 9, "WARNING": 3, "ERROR": 6})
        self.assertEqual(r.mal_formateadas, 17)
        self.assertIsNone(r.explicacion)  # el validador no explica

    def test_auditor_usuarios_solo_revisa_usuarios(self):
        r = crear_agente("auditor_usuarios").analizar_archivo(MALOS)
        codigos = {p.codigo for l in r.con_problemas for p in l.problemas}
        self.assertEqual(codigos, {"nombre_invalido", "correo_invalido"})
        # Líneas 14, 15, 16, 17, 18, 19, 20, 21 y 22 tienen nombre o correo inválido.
        self.assertEqual([l.numero for l in r.con_problemas], [14, 15, 16, 17, 18, 19, 20, 21, 22])
        # Los tipos se siguen contando aunque no use validar_nivel.
        self.assertEqual(r.por_tipo, {"INFO": 9, "WARNING": 3, "ERROR": 6})

    def test_analista_usa_la_ia(self):
        llm = LLMFalso("El problema más común son los correos.")
        r = crear_agente("analista", llm=llm).analizar_archivo(MALOS)
        self.assertEqual(r.explicacion, "El problema más común son los correos.")
        self.assertEqual(r.explicacion_fuente, "IA (claude-sonnet-5-5)")
        # El modelo recibe el resumen y las líneas con su motivo.
        enviado = llm.mensajes[0]
        self.assertIn("Líneas mal formateadas: 17", enviado)
        self.assertIn("Línea 22:", enviado)
        # Los conteos por tipo los calcula el programa, no la IA.
        self.assertIn("- Correo inválido: 5 (líneas 16, 17, 18, 20, 22)", enviado)
        self.assertIn("- Nombre inválido: 4 (líneas 14, 15, 19, 21)", enviado)
        self.assertIn("tiene dos puntos seguidos", enviado)

    def test_analista_sin_ia_usa_reglas(self):
        r = crear_agente("analista", motivo_sin_ia="desactivada con --sin-ia").analizar_archivo(MALOS)
        self.assertEqual(r.explicacion_fuente, "reglas, sin IA: desactivada con --sin-ia")
        self.assertIn("17 de 21 eventos tienen problemas", r.explicacion)
        # La línea 19 tiene correo válido (su problema es el nombre vacío).
        self.assertIn("Correo inválido: 5 (líneas 16, 17, 18, 20, 22)", r.explicacion)
        self.assertIn("Falta la fecha: 1 (línea 3)", r.explicacion)

    def test_analista_si_la_ia_falla_usa_reglas(self):
        llm = LLMFalso(error="no hay conexión con la API de Anthropic")
        r = crear_agente("analista", llm=llm).analizar_archivo(MALOS)
        self.assertEqual(r.explicacion_fuente, "reglas, sin IA: no hay conexión con la API de Anthropic")
        self.assertIn("Cómo corregirlo:", r.explicacion)

    def test_analista_archivo_sin_errores_no_llama_a_la_ia(self):
        llm = LLMFalso()
        r = crear_agente("analista", llm=llm).analizar_archivo(BUENOS)
        self.assertEqual(llm.mensajes, [])
        self.assertIn("No hay líneas con problemas", r.explicacion)


class TestConfiguracion(unittest.TestCase):
    """La personalización se hace en config/, sin tocar el código."""

    def setUp(self):
        self.carpeta = Path(tempfile.mkdtemp())
        shutil.copytree(CARPETA_CONFIG, self.carpeta, dirs_exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.carpeta)

    def editar(self, archivo, cambio):
        ruta = self.carpeta / archivo
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        cambio(datos)
        ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")

    def test_cambiar_una_regla_desde_json(self):
        self.editar("reglas.json", lambda d: d["nombre"].update(solo_letras=False))
        agente = crear_agente("validador", self.carpeta)
        ctx = agente.analizar_linea(1, "[INFO] 2025-01-13 Login usuario=Juan3 Pérez")
        self.assertEqual(ctx.problemas, [])

    def test_crear_agente_nuevo_solo_con_json(self):
        self.editar("agentes.json", lambda d: d.update(solo_fechas={
            "descripcion": "Solo revisa fechas",
            "skills_linea": ["parsear_linea", "validar_fecha"],
            "skills_reporte": ["resumir"],
        }))
        r = crear_agente("solo_fechas", self.carpeta).analizar_archivo(MALOS)
        codigos = {p.codigo for l in r.con_problemas for p in l.problemas}
        self.assertEqual(codigos, {"fecha_invalida", "falta_fecha"})

    def test_agente_con_skill_inexistente(self):
        self.editar("agentes.json", lambda d: d["validador"]["skills_linea"].append("validar_telefono"))
        with self.assertRaises(ErrorConfiguracion):
            crear_agente("validador", self.carpeta)

    def test_parsear_linea_debe_ir_primero(self):
        self.editar("agentes.json", lambda d: d["validador"]["skills_linea"].reverse())
        with self.assertRaises(ErrorConfiguracion):
            crear_agente("validador", self.carpeta)

    def test_agente_inexistente(self):
        with self.assertRaises(ErrorConfiguracion):
            crear_agente("no_existe", self.carpeta)


class TestArchivoEnv(unittest.TestCase):

    def test_cargar_env(self):
        import os
        from analizador.config import cargar_env
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / ".env"
            ruta.write_text('# comentario\nPRUEBA_CLAVE_ENV="valor de prueba"\n\nlinea sin igual\n', encoding="utf-8")
            os.environ.pop("PRUEBA_CLAVE_ENV", None)
            try:
                self.assertEqual(cargar_env(ruta), ["PRUEBA_CLAVE_ENV"])
                self.assertEqual(os.environ["PRUEBA_CLAVE_ENV"], "valor de prueba")
                # Una variable que ya existe no se sobrescribe.
                ruta.write_text("PRUEBA_CLAVE_ENV=otro\n", encoding="utf-8")
                self.assertEqual(cargar_env(ruta), [])
                self.assertEqual(os.environ["PRUEBA_CLAVE_ENV"], "valor de prueba")
            finally:
                os.environ.pop("PRUEBA_CLAVE_ENV", None)

    def test_sin_archivo_env(self):
        from analizador.config import cargar_env
        self.assertEqual(cargar_env(Path("no_existe/.env")), [])


class TestLineaDeComandos(unittest.TestCase):

    def ejecutar(self, *argumentos):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = main.main(list(argumentos))
        return codigo, salida.getvalue()

    def test_analista_sin_ia(self):
        codigo, salida = self.ejecutar(str(MALOS), "-a", "analista", "--sin-ia")
        self.assertEqual(codigo, 0)
        self.assertIn("Agente: analista", salida)
        self.assertIn("EXPLICACIÓN (reglas, sin IA: desactivada con --sin-ia)", salida)

    def test_listar(self):
        codigo, salida = self.ejecutar("--listar")
        self.assertEqual(codigo, 0)
        self.assertIn("auditor_usuarios", salida)
        self.assertIn("explicar_errores (reporte)", salida)

    def test_agente_inexistente(self):
        codigo, salida = self.ejecutar(str(MALOS), "-a", "no_existe")
        self.assertEqual(codigo, 2)
        self.assertIn("No existe el agente 'no_existe'", salida)

    def test_archivo_inexistente(self):
        codigo, salida = self.ejecutar("no_existe.txt")
        self.assertEqual(codigo, 1)
        self.assertIn("no existe", salida)


if __name__ == "__main__":
    unittest.main()
