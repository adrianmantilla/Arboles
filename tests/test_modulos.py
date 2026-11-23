"""Pruebas sin Maya de la fase 1: módulos, mallas, UVs y recetas."""

import math
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

from arboles import ejemplos, i18n  # noqa: E402
from arboles import modulos as mod  # noqa: E402
from arboles import vectores as v  # noqa: E402
from arboles.arbol import Arbol  # noqa: E402


def _arbol_sencillo(**rama):
    a = Arbol("prueba")
    t = a.anadir_tronco(altura=400, grosor=20, irregularidad=0, nudos=0, raices=0, curvatura=0)
    r = a.anadir_rama(t, **rama)
    return a.calcular(), t, r


class PruebaGuias(unittest.TestCase):
    def test_tronco_recto_mide_su_altura(self):
        a, t, _ = _arbol_sencillo()
        self.assertAlmostEqual(t.guia.largo, 400, delta=1e-6)
        self.assertAlmostEqual(t.guia.puntos[-1][1], 400, delta=1e-6)

    def test_rama_nace_en_el_eje_de_la_madre(self):
        a, t, r = _arbol_sencillo(posicion=0.5)
        self.assertLess(v.distancia(r.guia.puntos[0], t.guia.punto(0.5)), 1e-6)

    def test_rama_mas_fina_que_la_madre(self):
        a, t, r = _arbol_sencillo(grosor=0.5)
        self.assertAlmostEqual(r.guia.radio_base, t.guia.radio_medio(0.6) * 0.5, delta=1e-6)

    def test_la_caida_baja_la_punta(self):
        alturas = []
        for caida in (0.0, 0.5, 1.0):
            _, _, r = _arbol_sencillo(caida=caida, curvatura=0, angulo=80)
            alturas.append(r.guia.puntos[-1][1])
        self.assertGreater(alturas[0], alturas[1])
        self.assertGreater(alturas[1], alturas[2])

    def test_la_caida_nunca_pasa_de_vertical(self):
        _, _, r = _arbol_sencillo(caida=1.0, longitud=2000, grosor=0.05, angulo=10)
        for t in r.guia.tangentes:
            self.assertGreater(v.angulo_entre(t, v.ABAJO), 0.0)

    def test_marcos_ortonormales(self):
        a = ejemplos.copa_redonda().calcular()
        for m in a.modulos.values():
            for s in (0.0, 0.33, 0.77, 1.0):
                t, n, b = m.guia.marco(s)
                for x in (t, n, b):
                    self.assertAlmostEqual(v.largo(x), 1.0, places=6)
                self.assertAlmostEqual(v.punto(t, n), 0.0, places=6)

    def test_parametros_se_limitan(self):
        m = mod.Modulo("rama1", mod.RAMA, "tronco1", {"caida": 7, "nudos": 3.6})
        self.assertEqual(m.valores["caida"], 1.0)
        self.assertEqual(m.valores["nudos"], 4)

    def test_tronco_sin_madre_y_rama_con_madre(self):
        with self.assertRaises(ValueError):
            mod.Modulo("rama1", mod.RAMA, None)
        with self.assertRaises(ValueError):
            mod.Modulo("tronco1", mod.TRONCO, "x")


class PruebaMallas(unittest.TestCase):
    def setUp(self):
        self.arbol = ejemplos.copa_redonda()

    def test_mallas_coherentes_en_todos_los_niveles(self):
        for nivel in mod.NIVELES:
            for m in self.arbol.mallas(nivel):
                self.assertEqual(len(m.conexiones), sum(m.conteos))
                self.assertEqual(len(m.uv_ids), len(m.conexiones))
                self.assertEqual(len(m.us), len(m.vs))
                self.assertLess(max(m.conexiones), len(m.vertices))
                self.assertLess(max(m.uv_ids), len(m.us))

    def test_niveles_de_mas_a_menos_poligonos(self):
        cifras = [self.arbol.triangulos(n) for n in ("denso", "alto", "medio", "bajo")]
        self.assertEqual(cifras, sorted(cifras, reverse=True))
        self.assertLess(cifras[2], cifras[0] / 5.0)

    def test_presupuesto_para_un_jardin_de_50(self):
        # Medio debe caber holgado: 50 árboles distintos por debajo de un millón de triángulos.
        self.assertLess(self.arbol.triangulos("medio") * 50, 1000000)

    def test_mismo_contorno_en_denso_y_bajo(self):
        a = self.arbol.calcular()
        denso = {m.nombre: m for m in a.mallas("denso")}
        bajo = {m.nombre: m for m in a.mallas("bajo")}
        for nombre in denso:
            # El primer anillo (s = 0, theta = 0) es el mismo punto en las dos.
            self.assertLess(v.distancia(denso[nombre].vertices[0], bajo[nombre].vertices[0]), 1e-6)

    def test_uv_igual_en_cualquier_resolucion(self):
        a = self.arbol.calcular()
        for m in a.modulos.values():
            for nivel in ("denso", "bajo"):
                malla = mod.malla_tubo(m.guia, nivel, m.id, 0.0, a.escala_textura)
                lados = mod.lados(m.guia, nivel)
                n_seg = mod.segmentos(m.guia, nivel)
                # Última UV del último anillo: s = 1, theta = 2*pi
                i = n_seg * (lados + 1) + lados
                esperado = mod.uv(1.0, 2 * math.pi, m.guia, a.escala_textura)
                self.assertAlmostEqual(malla.us[i], esperado[0], places=9)
                self.assertAlmostEqual(malla.vs[i], esperado[1], places=9)

    def test_costura_en_vueltas_enteras(self):
        for radio in (0.5, 3, 25, 80):
            self.assertEqual(mod.repeticiones_u(radio, 60.0), int(mod.repeticiones_u(radio, 60.0)))
            self.assertGreaterEqual(mod.repeticiones_u(radio, 60.0), 1)

    def test_texel_parecido_en_tronco_y_rama(self):
        # Centímetros por repetición alrededor, frente a 60 a lo largo: no más del doble ni la mitad.
        a = self.arbol.calcular()
        for m in a.modulos.values():
            r = m.guia.radio_base
            cm_por_vuelta = 2 * math.pi * r / mod.repeticiones_u(r, a.escala_textura)
            if r > 60 / (2 * math.pi):
                self.assertTrue(30 <= cm_por_vuelta <= 120, (m.id, cm_por_vuelta))

    def test_normales_hacia_fuera(self):
        a, t, _ = _arbol_sencillo()
        m = mod.malla_tubo(t.guia, "medio", "t", 0.0)
        p = [m.vertices[i] for i in m.conexiones[:3]]
        normal = v.cruz(v.resta(p[1], p[0]), v.resta(p[2], p[0]))
        centro = t.guia.punto(0.0)
        hacia_fuera = v.resta(p[0], centro)
        self.assertGreater(v.punto(normal, hacia_fuera), 0)


class PruebaRecetas(unittest.TestCase):
    def test_ida_y_vuelta_en_json(self):
        a = ejemplos.copa_redonda()
        b = Arbol.de_json(a.a_json())
        self.assertEqual(a.a_dict(), b.a_dict())
        self.assertEqual(a.triangulos("bajo"), b.triangulos("bajo"))
        self.assertEqual(a.mallas("bajo")[3].vertices, b.mallas("bajo")[3].vertices)

    def test_quitar_rama_quita_sus_hijas(self):
        a = ejemplos.copa_redonda()
        rama = a.hijos("tronco1")[0]
        hijas = [h.id for h in a.hijos(rama.id)]
        a.quitar(rama.id)
        for id_ in [rama.id] + hijas:
            self.assertNotIn(id_, a.modulos)

    def test_receta_con_madre_inexistente(self):
        datos = ejemplos.copa_redonda().a_dict()
        datos["modulos"][1]["padre"] = "rama99"
        with self.assertRaises(ValueError):
            Arbol.de_dict(datos)

    def test_ids_no_se_repiten(self):
        a = ejemplos.copa_redonda()
        nuevo = a.anadir_rama("tronco1")
        self.assertEqual(len(a.modulos), len(set(a.modulos)))
        self.assertTrue(nuevo.id.startswith("rama"))

    def test_textos_de_niveles(self):
        for nivel in mod.NIVELES:
            self.assertIn("nivel_" + nivel, i18n.claves())


if __name__ == "__main__":
    unittest.main()


class PruebaHorquilla(unittest.TestCase):
    def _arbol(self, **tronco):
        from arboles.arbol import Arbol
        a = Arbol("y")
        t = a.anadir_tronco(altura=600, grosor=30, **tronco)
        arriba = a.anadir_rama(t, posicion=0.9, giro=10, longitud=200)
        abajo = a.anadir_rama(t, posicion=0.2, giro=10, longitud=200)
        return a.calcular(), t, arriba, abajo

    def test_sin_horquilla_igual_que_antes(self):
        a, t, arriba, _ = self._arbol()
        self.assertEqual(t.guia.brazos, [])
        self.assertEqual(arriba.guia.puntos[0], t.guia.punto(0.9))

    def test_se_divide_en_brazos(self):
        for brazos in (2, 3):
            a, t, arriba, abajo = self._arbol(horquilla=0.5, brazos=brazos, abertura=30)
            self.assertEqual(len(t.guia.brazos), brazos)
            for brazo in t.guia.brazos:
                self.assertEqual(brazo.puntos[0], t.guia.punto(0.5))
                self.assertGreater(brazo.punto(1.0)[1], t.guia.punto(0.5)[1] + 200)  # sube
            # La rama de arriba nace en un brazo, la de abajo en el tronco
            brazo, s = t.guia.sitio(0.9, 10)
            self.assertIn(brazo, t.guia.brazos)
            self.assertAlmostEqual(s, 0.8)
            self.assertEqual(arriba.guia.puntos[0], brazo.punto(s))
            self.assertEqual(abajo.guia.puntos[0], t.guia.punto(0.2))

    def test_brazos_separados_y_malla_unida(self):
        a, t, _, _ = self._arbol(horquilla=0.4, brazos=2, abertura=40)
        p1, p2 = (b.punto(1.0) for b in t.guia.brazos)
        self.assertGreater(abs(p1[0] - p2[0]) + abs(p1[2] - p2[2]), 150)
        malla = a.mallas("medio")[0]
        n = len(malla.vertices)
        self.assertTrue(all(0 <= i < n for i in malla.conexiones))
        self.assertTrue(all(0 <= i < len(malla.us) for i in malla.uv_ids))
        self.assertEqual(len(malla.uv_ids), len(malla.conexiones))

    def test_receta_guarda_la_horquilla(self):
        from arboles.arbol import Arbol
        a, t, _, _ = self._arbol(horquilla=0.5, brazos=3)
        b = Arbol.de_dict(a.a_dict()).calcular()
        self.assertEqual(len(b.tronco.guia.brazos), 3)
