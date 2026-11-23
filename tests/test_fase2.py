"""Pruebas sin Maya de la fase 2: follaje, curvas a mano, herramientas, semáforo y biblioteca."""

import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

from arboles import ejemplos, follaje, i18n  # noqa: E402
from arboles import modulos as mod  # noqa: E402
from arboles import vectores as v  # noqa: E402
from arboles.arbol import SEMAFORO, Arbol  # noqa: E402
from arboles.biblioteca import Biblioteca, nombre_de_archivo  # noqa: E402


def _arbol():
    a = Arbol("prueba")
    t = a.anadir_tronco(altura=500, grosor=20)
    r = a.anadir_rama(t, longitud=200, posicion=0.6)
    a.anadir_rama(r, longitud=80, posicion=0.5)
    return a, t.id, r.id


class Follaje(unittest.TestCase):
    def test_prototipos_validos(self):
        for tipo in follaje.TIPOS:
            alta, baja = follaje.prototipo(tipo, "alta"), follaje.prototipo(tipo, "baja")
            self.assertGreater(alta.triangulos, baja.triangulos)
            for m in (alta, baja):
                self.assertEqual(sum(m.conteos), len(m.conexiones))
                self.assertEqual(len(m.uv_ids), len(m.conexiones))
                self.assertLess(max(m.conexiones), len(m.vertices))
                self.assertLess(max(m.uv_ids), len(m.us))

    def test_colocar_repetible_y_vacio(self):
        a, _, r = _arbol()
        a.calcular()
        m = a.modulos[r]
        uno, dos = follaje.colocar(m), follaje.colocar(m)
        self.assertTrue(uno)
        self.assertEqual(uno, dos)
        for matriz in uno:
            self.assertEqual(len(matriz), 16)
        m.fijar("follaje", "ninguno")
        self.assertEqual(follaje.colocar(m), [])
        m.fijar("follaje", "aguja")
        m.fijar("densidad", 0)
        self.assertEqual(follaje.colocar(m), [])

    def test_mas_densidad_mas_grupos(self):
        a, _, r = _arbol()
        a.calcular()
        m = a.modulos[r]
        m.fijar("densidad", 0.2)
        pocos = len(follaje.colocar(m))
        m.fijar("densidad", 1.0)
        self.assertGreater(len(follaje.colocar(m)), pocos)

    def test_combinar(self):
        a, _, r = _arbol()
        a.calcular()
        matrices = follaje.colocar(a.modulos[r])
        base = follaje.prototipo("hoja_ancha", "alta")
        m = follaje.combinar("hoja_ancha", "denso", matrices)
        self.assertEqual(len(m.vertices), len(base.vertices) * len(matrices))
        self.assertEqual(m.triangulos, base.triangulos * len(matrices))
        self.assertLess(max(m.conexiones), len(m.vertices))
        self.assertLess(max(m.uv_ids), len(m.us))
        x, y, z = base.vertices[0]
        a0 = matrices[0]
        self.assertAlmostEqual(m.vertices[0][1], x * a0[1] + y * a0[5] + z * a0[9] + a0[13])

    def test_opcion_invalida(self):
        with self.assertRaises(ValueError):
            mod.limitar(mod.RAMA, "follaje", "palmera")


class CurvaAMano(unittest.TestCase):
    def test_control_desplaza_y_base_queda(self):
        a, _, r = _arbol()
        a.calcular()
        antes = a.modulos[r].guia.punto(1.0)
        a.modulos[r].fijar_control(2, (0.0, 50.0, 0.0))
        a.calcular()
        guia = a.modulos[r].guia
        self.assertAlmostEqual(guia.punto(1.0)[1] - antes[1], 50.0, places=3)
        self.assertAlmostEqual(v.distancia(guia.punto(0.0), guia.punto_base(0.0)), 0.0, places=6)

    def test_curva_en_receta(self):
        a, _, r = _arbol()
        a.modulos[r].fijar_control(1, (10.0, 0.0, -5.0))
        b = Arbol.de_json(a.a_json())
        self.assertEqual(b.modulos[r].a_dict(), a.modulos[r].a_dict())

    def test_mas_cercano(self):
        a, t, _ = _arbol()
        a.calcular()
        guia = a.modulos[t].guia
        s = guia.mas_cercano(v.suma(guia.punto(0.4), (30.0, 0.0, 0.0)))
        self.assertAlmostEqual(s, 0.4, delta=0.03)


class Herramientas(unittest.TestCase):
    def test_injertar_copia_con_ids_nuevos(self):
        a, t, r = _arbol()
        antes = len(a.modulos)
        raiz = a.injertar(a.subarbol(r), t, giro=90.0)
        self.assertEqual(len(a.modulos), antes + 2)
        self.assertNotEqual(raiz.id, r)
        self.assertEqual(raiz.valores["giro"], 90.0)
        self.assertEqual(len(a.hijos(raiz.id)), 1)

    def test_repetir_alrededor(self):
        a, t, r = _arbol()
        nuevas = a.repetir_alrededor(r, 4)
        self.assertEqual(len(nuevas), 4)
        giros = {round(m.valores["giro"], 3) for m in nuevas} | {a.modulos[r].valores["giro"]}
        self.assertEqual(len(giros), 5)
        self.assertEqual(len(a.hijos(t)), 5)
        with self.assertRaises(ValueError):
            a.repetir_alrededor(t, 2)

    def test_pegar_no_mueve_de_sitio(self):
        a, t, r = _arbol()
        otra = a.anadir_rama(t, posicion=0.3, giro=200.0)
        a.pegar_ajustes(dict(a.modulos[r].valores, posicion=0.9, giro=10.0, longitud=123.0), [otra.id])
        self.assertEqual(otra.valores["longitud"], 123.0)
        self.assertEqual(otra.valores["posicion"], 0.3)
        self.assertEqual(otra.valores["giro"], 200.0)

    def test_quitar_con_descendientes(self):
        a, t, r = _arbol()
        a.quitar(r)
        self.assertEqual(list(a.modulos), [t])


class Semaforo(unittest.TestCase):
    def test_plantillas(self):
        for nombre, plantilla in ejemplos.PLANTILLAS.items():
            color, triangulos = plantilla().semaforo()
            self.assertIn(color, ("verde", "amarillo", "rojo"))
            self.assertGreater(triangulos, 0)

    def test_follaje_cuenta(self):
        a, _, r = _arbol()
        con = a.triangulos("medio")
        sin = a.triangulos("medio", con_follaje=False)
        self.assertGreater(con, sin)

    def test_se_pone_rojo(self):
        a, t, r = _arbol()
        for _ in range(4):
            a.repetir_alrededor(r, 12)
        for m in list(a.modulos.values()):
            if m.tipo == mod.RAMA:
                m.fijar("densidad", 1.0)
                m.fijar("tamano_hoja", 0.3)
        color, triangulos = a.semaforo()
        self.assertGreater(triangulos, SEMAFORO[-1][0])
        self.assertEqual(color, "rojo")


class BibliotecaArboles(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def test_guardar_y_cargar(self):
        bib = Biblioteca(self.carpeta)
        self.assertEqual(bib.arboles(), [])
        a = ejemplos.PLANTILLAS["lloron"]()
        a.nombre = "Sauce del patio"
        bib.guardar(a)
        self.assertTrue(bib.existe("Sauce del patio"))
        self.assertEqual(bib.cargar("Sauce del patio").a_dict(), a.a_dict())
        self.assertTrue(bib.ruta_miniatura("Sauce del patio").endswith(".png"))

    def test_ramas_favoritas(self):
        bib = Biblioteca(self.carpeta)
        a, t, r = _arbol()
        bib.guardar_rama("Mi rama", a.subarbol(r))
        self.assertEqual(len(bib.ramas()), 1)
        nueva = a.injertar(bib.cargar_rama(bib.ramas()[0]), t)
        self.assertIn(nueva.id, a.modulos)

    def test_nombre_de_archivo(self):
        self.assertEqual(nombre_de_archivo("Árbol: ñandú/1"), "Arbol_nandu_1")
        self.assertEqual(nombre_de_archivo("///"), "arbol")


class Frondosidad(unittest.TestCase):
    def test_mas_frondosa_mas_hojas(self):
        for plantilla in ejemplos.PLANTILLAS:
            if plantilla == "vacio":
                continue
            tri = [ejemplos.crear(plantilla, f).triangulos("medio") for f in ejemplos.FRONDOSIDADES]
            self.assertLess(tri[0], tri[1], plantilla)
            self.assertLess(tri[1], tri[2], plantilla)
            self.assertEqual(ejemplos.crear(plantilla).a_dict(), ejemplos.PLANTILLAS[plantilla]().a_dict())

    def test_ninguna_roja(self):
        for plantilla in ejemplos.PLANTILLAS:
            for f in ejemplos.FRONDOSIDADES:
                self.assertNotEqual(ejemplos.crear(plantilla, f).semaforo()[0], "rojo", (plantilla, f))


class Textos(unittest.TestCase):
    def test_claves_dinamicas(self):
        claves = i18n.claves()
        faltan = []
        for tipo, parametros in mod.PARAMETROS.items():
            for nombre in parametros:
                for prefijo in ("p_", "ayuda_"):
                    if prefijo + tipo + "_" + nombre not in claves and prefijo + nombre not in claves:
                        faltan.append(prefijo + nombre)
        for opciones in mod.OPCIONES.values():
            faltan += ["opcion_" + o for o in opciones if "opcion_" + o not in claves]
        faltan += ["plantilla_" + p for p in ejemplos.PLANTILLAS if "plantilla_" + p not in claves]
        faltan += ["frondosidad_" + f for f in ejemplos.FRONDOSIDADES if "frondosidad_" + f not in claves]
        faltan += ["nivel_" + n for n in mod.NIVELES if "nivel_" + n not in claves]
        faltan += ["semaforo_" + c for c in ("verde", "amarillo", "rojo") if "semaforo_" + c not in claves]
        for boton in ("empezar", "abrir", "guardar", "anadir", "clic", "repetir", "quitar",
                      "copiar", "pegar", "favoritas", "enderezar", "plantar", "plantar_clic", "desligar",
                      "editar_maestro", "refrescar"):
            faltan += [c for c in ("boton_" + boton, "ayuda_boton_" + boton) if c not in claves]
        self.assertEqual(faltan, [])


if __name__ == "__main__":
    unittest.main()
