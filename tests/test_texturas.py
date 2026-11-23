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


    def test_estilo_y_vuelta_al_realista(self):
        real = self._imagen("roble", "1k", "corteza_color.jpg")
        normal_real = self._imagen("roble", "1k", "corteza_normal.jpg")
        cartoon = self._imagen(os.path.join("roble", "cartoon"), "1k", "corteza_color.jpg")
        self.assertEqual(tx.ruta("roble", "corteza", "color", "1k", self.carpeta, "cartoon"), cartoon)
        # El cartoon no trae normal: se usa la realista
        self.assertEqual(tx.ruta("roble", "corteza", "normal", "1k", self.carpeta, "cartoon"), normal_real)
        # Otro estilo que no está: el realista; y el realista nunca coge la del cartoon
        self.assertEqual(tx.ruta("roble", "corteza", "color", "1k", self.carpeta, "estilizado"), real)
        self.assertEqual(tx.ruta("roble", "corteza", "color", "1k", self.carpeta), real)
        # El estilo solo a 1K vale también para 2K (la más cercana dentro del estilo)
        self.assertEqual(tx.ruta("roble", "corteza", "color", "2k", self.carpeta, "cartoon"), cartoon)
        self.assertEqual(tx.estilos("roble", self.carpeta), ["realista", "cartoon"])
        self.assertEqual(tx.juegos(self.carpeta), ["roble"])

    def test_carpetas_extra(self):
        otra = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, otra)
        propia = os.path.join(otra, "mi_corteza", "1k", "corteza_color.png")
        os.makedirs(os.path.dirname(propia))
        open(propia, "wb").close()
        antes = list(tx.CARPETAS_EXTRA)
        self.addCleanup(lambda: tx.CARPETAS_EXTRA.__setitem__(slice(None), antes))
        tx.CARPETAS_EXTRA[:] = [otra]
        self.assertIn("mi_corteza", tx.juegos())
        self.assertIn("roble", tx.juegos())
        self.assertTrue(tx.existe("mi_corteza"))
        self.assertEqual(tx.ruta("mi_corteza", "corteza", "color", "2k"), propia)


class PruebaTexturasDeSerie(unittest.TestCase):
    def test_cada_especie_trae_sus_estilos(self):
        for especie in especies.ESPECIES:
            self.assertEqual(tx.estilos(especie), list(tx.ESTILOS), especie)
            for estilo in ("cartoon", "estilizado"):
                color = tx.ruta(especie, "corteza", "color", "1k", estilo=estilo)
                self.assertIn(os.sep + estilo + os.sep, color, (especie, estilo))


    def test_cada_especie_trae_sus_hojas(self):
        for especie, receta in especies.ESPECIES.items():
            if all(m.valores.get("follaje", "ninguno") == "ninguno" for m in receta().modulos.values()):
                continue  # sin follaje (árbol seco): no necesita hojas
            canales = tx.canales(especie, "hoja", "1k")
            self.assertEqual(sorted(canales), sorted(tx.CANALES), especie)
            # 2K y 4K no hacen falta en las hojas: se usa la más cercana.
            self.assertEqual(tx.ruta(especie, "hoja", "color", "4k"), canales["color"])

    # Las cortezas se generan en un ordenador con Substance Designer: las que ya están en el plugin
    CON_CORTEZA = ("roble", "haya", "pino_pinonero", "abeto", "abedul", "sauce_lloron", "cipres", "olivo",
                   "arbusto", "encina", "platano", "chopo", "castano", "arce", "arce_otono",
                   "palmera", "almendro", "alcornoque", "arbol_seco")

    def test_cada_especie_trae_su_corteza(self):
        for especie in self.CON_CORTEZA:
            for res in ("512", "1k", "2k"):
                canales = tx.canales(especie, "corteza", res)
                self.assertEqual(sorted(canales), ["color", "normal", "rugosidad"], (especie, res))
                self.assertIn(os.sep + res + os.sep, canales["color"])

    def test_nombres_de_archivo_conocidos(self):
        def revisar(carpeta, juego, estilo=None):
            for res in os.listdir(carpeta):
                if estilo is None and res in tx.ESTILOS:
                    revisar(os.path.join(carpeta, res), juego, res)
                    continue
                self.assertIn(res, tx.RESOLUCIONES, (juego, estilo, res))
                for nombre in os.listdir(os.path.join(carpeta, res)):
                    parte, _, resto = nombre.partition("_")
                    self.assertIn(parte, tx.PARTES, (juego, res, nombre))
                    self.assertIn(os.path.splitext(resto)[0], tx.CANALES, (juego, res, nombre))

        for juego in tx.juegos(tx.carpeta_texturas()):
            revisar(os.path.join(tx.carpeta_texturas(), juego), juego)


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


class PruebaMaterialesPropios(unittest.TestCase):
    def setUp(self):
        from arboles import materiales_propios as mp
        self.mp = mp
        self.bib = tempfile.mkdtemp()
        self.origen = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.bib)
        self.addCleanup(shutil.rmtree, self.origen)
        antes = list(tx.CARPETAS_EXTRA)
        self.addCleanup(lambda: tx.CARPETAS_EXTRA.__setitem__(slice(None), antes))

    def _img(self, nombre):
        ruta = os.path.join(self.origen, nombre)
        with open(ruta, "wb") as f:
            f.write(b"x")
        return ruta

    def test_crear_y_usar(self):
        juego = self.mp.crear(self.bib, "Mi Corteza Áspera", {
            ("corteza", "color"): self._img("c.PNG"), ("corteza", "normal"): self._img("n.jpeg")})
        self.assertEqual(juego, "propio_mi_corteza_aspera")
        self.mp.registrar(self.bib)
        self.assertTrue(tx.existe(juego))
        self.assertEqual(self.mp.lista(self.bib), [juego])
        self.assertEqual(self.mp.nombre_visible(juego), "Mi Corteza Áspera")
        self.assertTrue(tx.ruta(juego, "corteza", "color", "2k").endswith(os.path.join("1k", "corteza_color.png")))
        self.assertTrue(tx.ruta(juego, "corteza", "normal", "512").endswith("corteza_normal.jpg"))
        self.assertIsNone(tx.ruta(juego, "hoja", "color"))
        # Los estilos caen al realista: el material propio se ve igual en cartoon
        self.assertEqual(tx.ruta(juego, "corteza", "color", estilo="cartoon"), tx.ruta(juego, "corteza", "color"))

    def test_rehacer_quita_las_imagenes_viejas(self):
        self.mp.crear(self.bib, "m", {("corteza", "color"): self._img("a.png"), ("corteza", "normal"): self._img("b.png")})
        juego = self.mp.crear(self.bib, "m", {("hoja", "color"): self._img("h.png")})
        self.mp.registrar(self.bib)
        self.assertIsNone(tx.ruta(juego, "corteza", "normal"))
        self.assertIsNotNone(tx.ruta(juego, "hoja", "color"))

    def test_hace_falta_un_color(self):
        with self.assertRaises(ValueError):
            self.mp.crear(self.bib, "m", {("corteza", "normal"): self._img("n.png")})
        with self.assertRaises(ValueError):
            self.mp.crear(self.bib, "m", {("corteza", "color"): self._img("c.psd")})

    def test_no_choca_con_las_especies(self):
        self.assertTrue(self.mp.nombre_juego("roble").startswith("propio_"))
        self.assertFalse(self.mp.es_propio("roble"))
