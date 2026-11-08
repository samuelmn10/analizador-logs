"""
Pruebas automáticas del analizador.

Ejecutar con:
    python -m unittest -v test_analizador.py

Cada prueba documenta un caso borde y el resultado ESPERADO según las
reglas definidas en analizador_logs.py. Si cambias una regla, ajusta
también la prueba correspondiente.
"""

import unittest
from pathlib import Path

from analizador_logs import analizar_archivo, analizar_linea

CARPETA_PRUEBAS = Path(__file__).parent / "pruebas"


class TestLineas(unittest.TestCase):

    def test_linea_correcta(self):
        r = analizar_linea("[INFO] 2025-01-10 User logged in")
        self.assertEqual(r["nivel"], "INFO")
        self.assertEqual(r["fecha"], "valida")
        self.assertEqual(r["mensaje"], "User logged in")
        self.assertEqual(r["problemas"], [])

    def test_sin_fecha(self):
        r = analizar_linea("[WARNING] Invalid password attempt")
        self.assertEqual(r["nivel"], "WARNING")
        self.assertEqual(r["fecha"], "ausente")
        self.assertIn("falta la fecha", r["problemas"])

    def test_fecha_imposible(self):
        # Una regex simple \d{4}-\d{2}-\d{2} aceptaría esta fecha.
        r = analizar_linea("[ERROR] 2025-13-45 Impossible date")
        self.assertEqual(r["fecha"], "invalida")

    def test_30_de_febrero(self):
        r = analizar_linea("[INFO] 2025-02-30 No existe")
        self.assertEqual(r["fecha"], "invalida")

    def test_fecha_otro_formato(self):
        r = analizar_linea("[INFO] 10/01/2025 Otro formato")
        self.assertEqual(r["fecha"], "invalida")

    def test_nivel_en_minusculas(self):
        r = analizar_linea("[info] 2025-01-10 minúsculas")
        self.assertEqual(r["nivel"], "INFO")

    def test_nivel_desconocido(self):
        r = analizar_linea("[DEBUG] 2025-01-10 Algo")
        self.assertIsNone(r["nivel"])
        self.assertTrue(r["problemas"])

    def test_sin_corchetes(self):
        r = analizar_linea("User logged in")
        self.assertIsNone(r["nivel"])
        self.assertIn("no tiene nivel entre corchetes", r["problemas"])

    def test_sin_mensaje(self):
        r = analizar_linea("[INFO] 2025-01-10")
        self.assertIn("falta el mensaje", r["problemas"])

    def test_linea_vacia_se_ignora(self):
        self.assertIsNone(analizar_linea("   \n"))


class TestNombres(unittest.TestCase):

    def test_nombre_valido_con_tildes_y_enie(self):
        r = analizar_linea("[INFO] 2025-01-13 Login usuario=María Muñoz")
        self.assertEqual(r["problemas"], [])

    def test_nombre_en_minusculas(self):
        r = analizar_linea("[INFO] 2025-01-13 Login usuario=juan pérez")
        self.assertTrue(any("mayúscula" in p for p in r["problemas"]))

    def test_nombre_sin_apellido(self):
        r = analizar_linea("[INFO] 2025-01-13 Login usuario=Juan")
        self.assertTrue(any("nombre y apellido" in p for p in r["problemas"]))

    def test_nombre_vacio(self):
        r = analizar_linea("[INFO] 2025-01-13 Login usuario= correo=a@b.com")
        self.assertTrue(any("vacío" in p for p in r["problemas"]))

    def test_nombre_con_numero_se_rechaza(self):
        # Decisión: NOMBRE_SOLO_LETRAS = True.
        r = analizar_linea("[INFO] 2025-01-13 Login usuario=Juan3 Pérez")
        self.assertTrue(any("solo puede tener letras" in p for p in r["problemas"]))

    def test_nombre_con_simbolo_se_rechaza(self):
        r = analizar_linea("[INFO] 2025-01-13 Login usuario=Juan_P Pérez")
        self.assertTrue(any("solo puede tener letras" in p for p in r["problemas"]))

    def test_linea_sin_campos_no_es_error(self):
        r = analizar_linea("[INFO] 2025-01-13 Backup completed")
        self.assertEqual(r["problemas"], [])


class TestCorreos(unittest.TestCase):

    def test_correo_valido(self):
        r = analizar_linea("[INFO] 2025-01-13 Reset correo=soporte@empresa.com.sv")
        self.assertEqual(r["problemas"], [])

    def test_correo_sin_arroba(self):
        r = analizar_linea("[INFO] 2025-01-13 Reset correo=ana.gmail.com")
        self.assertTrue(any("falta la @" in p for p in r["problemas"]))

    def test_correo_sin_dominio(self):
        r = analizar_linea("[INFO] 2025-01-13 Reset correo=ana@gmail")
        self.assertTrue(any("dominio" in p for p in r["problemas"]))

    def test_correo_sin_identificador(self):
        r = analizar_linea("[INFO] 2025-01-13 Reset correo=@gmail.com")
        self.assertTrue(any("identificador" in p for p in r["problemas"]))

    def test_correo_doble_arroba(self):
        r = analizar_linea("[INFO] 2025-01-13 Reset correo=ana@@gmail.com")
        self.assertTrue(any("más de una @" in p for p in r["problemas"]))

    def test_correo_con_simbolo_no_permitido(self):
        r = analizar_linea("[INFO] 2025-01-13 Reset correo=ana!@gmail.com")
        self.assertTrue(r["problemas"])


class TestArchivos(unittest.TestCase):

    def test_archivo_bien_formado(self):
        r = analizar_archivo(CARPETA_PRUEBAS / "logs_buenos.txt")
        self.assertEqual(r["total_eventos"], 11)
        self.assertEqual(r["por_tipo"], {"INFO": 6, "WARNING": 3, "ERROR": 2})
        self.assertEqual(r["mal_formateadas"], 0)

    def test_archivo_con_errores(self):
        r = analizar_archivo(CARPETA_PRUEBAS / "logs_malos.txt")
        self.assertEqual(r["total_eventos"], 20)
        self.assertEqual(r["por_tipo"], {"INFO": 8, "WARNING": 3, "ERROR": 6})
        self.assertEqual(r["mal_formateadas"], 16)


if __name__ == "__main__":
    unittest.main()
