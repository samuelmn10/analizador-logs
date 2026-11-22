"""Pruebas de cada skill por separado y del registro de skills."""

import unittest

from analizador import skills
from analizador.agente import Entorno
from analizador.config import ErrorConfiguracion, Reglas, ReglasNombre
from analizador.modelos import LineaContexto
from analizador.skills.validar_correo import motivo_correo
from analizador.skills.validar_nombre import motivos_nombre


def procesar(texto, *nombres, reglas=None):
    """Ejecuta parsear_linea y luego las skills indicadas sobre una línea."""
    entorno = Entorno(reglas=reglas or Reglas(), sugerencias={}, definicion=None)
    ctx = LineaContexto(numero=1, texto=texto)
    for nombre in ("parsear_linea",) + nombres:
        skills.obtener(nombre, "linea").funcion(ctx, entorno)
    return ctx


class TestRegistro(unittest.TestCase):

    def test_skills_registradas(self):
        esperadas = {"parsear_linea", "validar_nivel", "validar_fecha", "validar_mensaje",
                     "validar_nombre", "validar_correo", "resumir", "explicar_errores"}
        self.assertEqual(set(skills.REGISTRO), esperadas)

    def test_skill_desconocida(self):
        with self.assertRaises(ErrorConfiguracion):
            skills.obtener("no_existe", "linea")

    def test_tipo_incorrecto(self):
        with self.assertRaises(ErrorConfiguracion):
            skills.obtener("resumir", "linea")


class TestParsearLinea(unittest.TestCase):

    def test_extrae_sin_validar(self):
        ctx = procesar("[ERROR] 2025-13-45 Algo")
        self.assertEqual(ctx.nivel, "ERROR")
        self.assertEqual(ctx.fecha_texto, "2025-13-45")
        self.assertEqual(ctx.mensaje, "Algo")
        self.assertEqual(ctx.problemas, [])  # parsear no valida

    def test_linea_vacia(self):
        self.assertTrue(procesar("   ").vacia)

    def test_sin_corchetes(self):
        self.assertFalse(procesar("texto suelto").tiene_corchetes)


class TestValidaciones(unittest.TestCase):

    def codigos(self, ctx):
        return [p.codigo for p in ctx.problemas]

    def test_validar_nivel(self):
        self.assertEqual(self.codigos(procesar("sin nivel", "validar_nivel")), ["sin_corchetes"])
        self.assertEqual(self.codigos(procesar("[] 2025-01-01 x", "validar_nivel")), ["nivel_vacio"])
        self.assertEqual(self.codigos(procesar("[DEBUG] 2025-01-01 x", "validar_nivel")), ["nivel_desconocido"])

    def test_validar_fecha(self):
        self.assertEqual(self.codigos(procesar("[INFO] 2025-02-30 x", "validar_fecha")), ["fecha_invalida"])
        self.assertEqual(self.codigos(procesar("[INFO] sin fecha", "validar_fecha")), ["falta_fecha"])
        self.assertEqual(procesar("[INFO] 2025-01-10 x", "validar_fecha").fecha, "valida")

    def test_validar_mensaje(self):
        self.assertEqual(self.codigos(procesar("[INFO] 2025-01-10", "validar_mensaje")), ["falta_mensaje"])

    def test_validar_nombre_y_correo_juntos(self):
        ctx = procesar("[INFO] 2025-01-13 Login usuario=juan correo=juan@gmail",
                       "validar_nombre", "validar_correo")
        self.assertEqual(self.codigos(ctx), ["nombre_invalido", "correo_invalido"])

    def test_skill_aislada_no_revisa_otras_cosas(self):
        # validar_correo sola no se queja de la fecha imposible: cada skill
        # hace una sola cosa.
        ctx = procesar("[INFO] 2025-13-45 x correo=ana@gmail.com", "validar_correo")
        self.assertEqual(ctx.problemas, [])


class TestFuncionesReutilizables(unittest.TestCase):

    def test_motivo_correo(self):
        self.assertIsNone(motivo_correo("soporte@empresa.com.sv"))
        self.assertEqual(motivo_correo("ana..lopez@gmail.com"), "tiene dos puntos seguidos")

    def test_motivos_nombre_con_otras_reglas(self):
        # Las reglas llegan como parámetro: la misma función sirve para
        # configuraciones distintas.
        permisivas = ReglasNombre(minimo_dos_palabras=False, solo_letras=False)
        self.assertEqual(motivos_nombre("Juan3", permisivas), [])
        self.assertIn("solo puede tener letras", motivos_nombre("Juan3 Pérez", ReglasNombre()))


if __name__ == "__main__":
    unittest.main()
