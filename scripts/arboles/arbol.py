"""Un árbol: sus módulos, su receta en JSON y sus mallas por nivel de detalle.

La receta guarda solo parámetros, nunca mallas: con ella el árbol se vuelve a
construir a cualquier resolución, en cualquier escena.
"""

import json

from arboles import modulos as mod

VERSION_RECETA = 1


class Arbol(object):
    def __init__(self, nombre="arbol", escala_textura=60.0):
        self.nombre = nombre
        self.escala_textura = float(escala_textura)  # cm que ocupa una repetición de la textura de corteza
        self.modulos = {}   # id -> Modulo, en orden de creación
        self._contador = {}

    # --- edición ---

    def _nuevo_id(self, tipo):
        n = self._contador.get(tipo, 0) + 1
        while "{}{}".format(tipo, n) in self.modulos:
            n += 1
        self._contador[tipo] = n
        return "{}{}".format(tipo, n)

    @property
    def tronco(self):
        return next((m for m in self.modulos.values() if m.tipo == mod.TRONCO), None)

    def anadir_tronco(self, **valores):
        if self.tronco:
            raise ValueError("el árbol ya tiene tronco")
        m = mod.Modulo(self._nuevo_id(mod.TRONCO), mod.TRONCO, None, valores)
        self.modulos[m.id] = m
        return m

    def anadir_rama(self, padre, **valores):
        padre = getattr(padre, "id", padre)
        if padre not in self.modulos:
            raise KeyError("no existe el módulo {}".format(padre))
        m = mod.Modulo(self._nuevo_id(mod.RAMA), mod.RAMA, padre, valores)
        self.modulos[m.id] = m
        return m

    def hijos(self, id_):
        return [m for m in self.modulos.values() if m.padre == id_]

    def quitar(self, id_):
        """Quita el módulo y todo lo que cuelga de él."""
        for hijo in self.hijos(id_):
            self.quitar(hijo.id)
        self.modulos.pop(id_, None)

    # --- cálculo ---

    def _orden(self):
        """Módulos con cada madre antes que sus hijas."""
        hechos, orden = set(), []
        pendientes = list(self.modulos.values())
        while pendientes:
            avance = False
            for m in list(pendientes):
                if m.padre is None or m.padre in hechos:
                    orden.append(m)
                    hechos.add(m.id)
                    pendientes.remove(m)
                    avance = True
            if not avance:
                raise ValueError("hay ramas sin madre: {}".format([m.id for m in pendientes]))
        return orden

    def calcular(self):
        for m in self._orden():
            if m.tipo == mod.TRONCO:
                m.guia = mod.guia_tronco(m)
            else:
                m.guia = mod.guia_rama(m, self.modulos[m.padre].guia)
        return self

    def mallas(self, nivel="denso"):
        self.calcular()
        return [mod.malla_tubo(m.guia, nivel, m.id, m.valores["torsion"], self.escala_textura)
                for m in self._orden()]

    def triangulos(self, nivel):
        return sum(malla.triangulos for malla in self.mallas(nivel))

    # --- receta ---

    def a_dict(self):
        return {"version": VERSION_RECETA, "nombre": self.nombre, "escala_textura": self.escala_textura,
                "modulos": [m.a_dict() for m in self.modulos.values()]}

    def a_json(self):
        return json.dumps(self.a_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def de_dict(cls, datos):
        arbol = cls(datos.get("nombre", "arbol"), datos.get("escala_textura", 60.0))
        for d in datos.get("modulos", []):
            m = mod.Modulo.de_dict(d)
            arbol.modulos[m.id] = m
        arbol._orden()  # valida madres
        return arbol

    @classmethod
    def de_json(cls, texto):
        return cls.de_dict(json.loads(texto))
