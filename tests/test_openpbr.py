"""Materiales en OpenPBR y conversión de escenas viejas, con un Maya falso.

Ejecutar desde la raíz del repositorio:  python -m unittest discover tests
"""

import importlib
import os
import sys
import unittest
from unittest import mock

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "scripts"))
sys.path.insert(0, AQUI)

import arboles  # noqa: E402
import maya_nombres  # noqa: E402

_CON_MAYA = ("arboles.openpbr", "arboles.materiales")


class PruebasOpenPBR(unittest.TestCase):
    def setUp(self):
        antes = {n: getattr(arboles, n.split(".")[1], None) for n in _CON_MAYA}
        self.addCleanup(lambda: [setattr(arboles, n.split(".")[1], m)
                                 for n, m in antes.items() if m is not None])
        self.escena, modulos = maya_nombres.instalar()
        for nombre in _CON_MAYA:
            modulos[nombre] = None
        parche = mock.patch.dict(sys.modules, modulos)
        parche.start()
        self.addCleanup(parche.stop)
        for nombre in _CON_MAYA:
            del sys.modules[nombre]
            if hasattr(arboles, nombre.split(".")[1]):
                delattr(arboles, nombre.split(".")[1])
        self.materiales = importlib.import_module("arboles.materiales")
        self.cmds = sys.modules["maya.cmds"]

    def _entra(self, nodo, atributo):
        destino = self.escena.buscar(nodo)
        for o, _a, d, b in self.escena.conexiones:
            if d is destino and b == atributo:
                return o.nombre
        return None

    def test_clay_en_openpbr(self):
        material, grupo = self.materiales.crear_material("arboles_clay_hoja")
        self.assertEqual(self.cmds.nodeType(material), "openPBRSurface")
        self.assertEqual(self.cmds.getAttr(material + ".specularWeight"), 0.35)
        self.assertEqual(self.cmds.getAttr(material + ".subsurfaceWeight"), 0.15)
        self.assertEqual(self.cmds.getAttr(material + ".geometryThinWalled"), 1)
        self.assertEqual(self._entra(grupo, "surfaceShader"), material)

    def test_sin_openpbr_usa_standard_surface(self):
        with mock.patch.object(self.cmds, "allNodeTypes", lambda **_: ["standardSurface"]):
            material, _ = self.materiales.crear_material("arboles_clay_corteza")
        self.assertEqual(self.cmds.nodeType(material), "standardSurface")
        self.assertEqual(self.cmds.getAttr(material + ".specular"), 0.3)

    def test_convertir_escena_vieja(self):
        with mock.patch.object(self.cmds, "allNodeTypes", lambda **_: ["standardSurface"]):
            material, grupo = self.materiales.crear_material("arboles_clay_hoja")
        imagen = self.cmds.shadingNode("file", name="arboles_clay_hoja_color")
        self.cmds.connectAttr(imagen + ".outColor", material + ".baseColor")
        self.cmds.setAttr(material + ".emission", 0.35)
        hechos = self.materiales.convertir_a_openpbr()
        self.assertEqual(hechos, ["arboles_clay_hoja"])
        self.assertEqual(self.cmds.nodeType("arboles_clay_hoja"), "openPBRSurface")
        self.assertEqual(self.cmds.getAttr("arboles_clay_hoja.specularWeight"), 0.35)
        self.assertEqual(self.cmds.getAttr("arboles_clay_hoja.subsurfaceWeight"), 0.15)
        self.assertAlmostEqual(self.cmds.getAttr("arboles_clay_hoja.emissionLuminance"), 350.0)
        self.assertEqual(self._entra("arboles_clay_hoja", "baseColor"), imagen)
        self.assertEqual(self._entra(grupo, "surfaceShader"), "arboles_clay_hoja")
        self.assertEqual(self.materiales.convertir_a_openpbr(), [])


if __name__ == "__main__":
    unittest.main()
