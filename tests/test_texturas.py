"""Pruebas sin Maya de los juegos de texturas por especie."""

import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

from arboles import especies, i18n  # noqa: E402
from arboles import texturas as tx  # noqa: E402
from arboles.arbol import Arbol  # noqa: E402


class PruebaTexturas(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.carpeta)

    def _imagen(self, juego, res, nombre):
        ruta = os.path.join(self.carpeta, juego, res, nombre)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        open(ruta, "wb").close()
        return ruta

    def test_sin_carpeta_no_hay_juegos(self):
        self.assertEqual(tx.juegos(os.path.join(self.carpeta, "no_existe")), [])

    def test_clay_nunca_es_un_juego(self):
        os.makedirs(os.path.join(self.carpeta, "clay"))
        self.assertFalse(tx.existe("clay", self.carpeta))
        self.assertFalse(tx.existe("", self.carpeta))

    def test_juego_instalado(self):
        self._imagen("roble", "1k", "corteza_color.png")
        os.makedirs(os.path.join(self.carpeta, ".oculta"))
        self.assertEqual(tx.juegos(self.carpeta), ["roble"])
        self.assertTrue(tx.existe("roble", self.carpeta))
        self.assertFalse(tx.existe("haya", self.carpeta))

    def test_resolucion_exacta(self):
        self._imagen("roble", "1k", "corteza_color.png")
        esperado = self._imagen("roble", "2k", "corteza_color.jpg")
        self.assertEqual(tx.ruta("roble", "corteza", "color", "2k", self.carpeta), esperado)

    def test_resolucion_mas_cercana(self):
        uno = self._imagen("roble", "1k", "hoja_color.png")
        cuatro = self._imagen("roble", "4k", "hoja_color.png")
        # 2K no está: entre 1K y 4K, la más cercana es 1K.
        self.assertEqual(tx.ruta("roble", "hoja", "color", "2k", self.carpeta), uno)
        self.assertEqual(tx.ruta("roble", "hoja", "color", "4k", self.carpeta), cuatro)
        self.assertEqual(tx.ruta("roble", "hoja", "color", "512", self.carpeta), uno)
        self.assertEqual(tx.ruta("roble", "hoja", "color", "rara", self.carpeta), uno)

    def test_canales_presentes(self):
        for canal in ("color", "normal", "rugosidad"):
            self._imagen("haya", "1k", "corteza_{}.png".format(canal))
        self._imagen("haya", "1k", "hoja_translucidez.tif")
        self.assertEqual(sorted(tx.canales("haya", "corteza", "1k", self.carpeta)),
                         ["color", "normal", "rugosidad"])
        self.assertEqual(list(tx.canales("haya", "hoja", "1k", self.carpeta)), ["translucidez"])
        self.assertIsNone(tx.ruta("haya", "hoja", "normal", "1k", self.carpeta))

    def test_extension_desconocida_no_cuenta(self):
        self._imagen("olivo", "1k", "corteza_color.psd")
        self.assertIsNone(tx.ruta("olivo", "corteza", "color", "1k", self.carpeta))


class PruebaMaterialDelArbol(unittest.TestCase):
    def test_por_defecto_clay(self):
        self.assertEqual(Arbol("x").material, tx.CLAY)

    def test_cada_especie_pide_su_juego(self):
        for nombre, crear in especies.ESPECIES.items():
            self.assertEqual(crear().material, nombre)

    def test_material_viaja_en_la_receta(self):
        a = especies.ESPECIES["roble"]()
        self.assertEqual(Arbol.de_json(a.a_json()).material, "roble")

    def test_textos_de_resolucion(self):
        claves = i18n.claves()
        for res in tx.RESOLUCIONES:
            self.assertIn("resolucion_" + res, claves)
        for clave in ("material", "ayuda_material", "material_clay", "material_sin_texturas", "menu_resolucion"):
            self.assertIn(clave, claves)


if __name__ == "__main__":
    unittest.main()
