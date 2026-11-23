"""Pruebas sin Maya de la fase 0: ajustes, textos e instalador."""

import json
import os
import re
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
sys.path.insert(0, RAIZ)

from arboles import ajustes as aj  # noqa: E402
from arboles import i18n  # noqa: E402
import instalar  # noqa: E402


class PruebaAjustes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.prefs = os.path.join(self.tmp.name, "prefs", "arboles")

    def tearDown(self):
        self.tmp.cleanup()

    def test_primer_uso_sin_archivo(self):
        self.assertTrue(aj.Ajustes(self.prefs).primer_uso())

    def test_fijar_crea_carpetas_y_persiste(self):
        biblioteca = os.path.join(self.tmp.name, "Mis cosas", "Árboles")
        ruta = aj.Ajustes(self.prefs).fijar_biblioteca(biblioteca)
        for sub in aj.SUBCARPETAS_BIBLIOTECA:
            self.assertTrue(os.path.isdir(os.path.join(ruta, sub)))
        otra = aj.Ajustes(self.prefs)
        self.assertFalse(otra.primer_uso())
        self.assertEqual(otra.carpeta_biblioteca, ruta)
        self.assertTrue(aj.se_puede_escribir(ruta))

    def test_json_roto_equivale_a_primer_uso(self):
        os.makedirs(self.prefs)
        with open(os.path.join(self.prefs, "ajustes.json"), "w") as f:
            f.write("{roto")
        self.assertTrue(aj.Ajustes(self.prefs).primer_uso())

    def test_biblioteca_por_defecto_en_documentos(self):
        ruta = aj.biblioteca_por_defecto()
        self.assertEqual(os.path.basename(ruta), "Arboles")
        self.assertEqual(os.path.basename(os.path.dirname(ruta)), "Documents")

    def test_no_se_puede_escribir_en_carpeta_inexistente(self):
        self.assertFalse(aj.se_puede_escribir(os.path.join(self.tmp.name, "no_existe")))
        self.assertFalse(aj.se_puede_escribir(None))


class PruebaTextos(unittest.TestCase):
    def test_todas_las_claves_usadas_existen(self):
        usadas = set()
        for carpeta, _, archivos in os.walk(os.path.join(RAIZ, "scripts")):
            for nombre in archivos:
                if nombre.endswith(".py"):
                    with open(os.path.join(carpeta, nombre), encoding="utf-8") as f:
                        usadas |= set(re.findall(r'\bt\("([a-z_]+)"[,)]', f.read()))
        with open(os.path.join(RAIZ, "scripts", "arboles", "interfaz_maya.py"), encoding="utf-8") as f:
            usadas |= set(re.findall(r'_proximamente\("([a-z_]+)"\)', f.read()))
        faltan = usadas - i18n.claves()
        self.assertFalse(faltan, "Faltan en es.json: {}".format(sorted(faltan)))

    def test_es_json_valido_y_sin_vacios(self):
        with open(os.path.join(RAIZ, "scripts", "arboles", "i18n", "es.json"), encoding="utf-8") as f:
            datos = json.load(f)
        self.assertTrue(all(isinstance(v, str) and v for v in datos.values()))

    def test_sustitucion_y_clave_desconocida(self):
        self.assertIn("/x", i18n.t("carpeta_lista", ruta="/x"))
        self.assertEqual(i18n.t("no_existe"), "no_existe")


class PruebaInstalador(unittest.TestCase):
    def test_mod_con_barras_normales(self):
        texto = instalar.contenido_mod("C:\\Users\\Ana\\Arboles", "0.0.1")
        self.assertTrue(texto.startswith("+ Arboles 0.0.1 C:/Users/Ana/Arboles\n"))
        self.assertIn("scripts: scripts", texto)
        self.assertIn("plug-ins: plug-ins", texto)

    def test_version_coincide_con_el_paquete(self):
        import arboles
        self.assertEqual(instalar._version(RAIZ), arboles.__version__)

    def test_ruta_mod_sin_tildes(self):
        modulos = os.path.join("C:", os.sep, "Users", "José", "Documents", "maya", "modules")
        raiz = os.path.join("C:", os.sep, "Users", "José", "Documents", "Plugins", "Arboles")
        rel = instalar.ruta_para_mod(raiz, modulos)
        self.assertTrue(rel.isascii())
        self.assertEqual(os.path.normpath(os.path.join(modulos, rel)), os.path.normpath(raiz))
        self.assertEqual(instalar.ruta_para_mod("/Users/ana/Arboles", modulos), "/Users/ana/Arboles")


if __name__ == "__main__":
    unittest.main()
