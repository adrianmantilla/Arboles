"""Render con Arnold del catálogo: todas las plantillas en fila (herramienta de desarrollo, fase 4).

    mayapy herramientas/render_catalogo.py /ruta/de/salida [--cerca]

Deja catalogo.png (las plantillas en frondosidad normal, calidad media, cada
una con las texturas de su especie si están instaladas) y catalogo_hojas.png
(un grupo de cada tipo de hoja, de cerca). Con --cerca, además, cerca_<especie>.png:
cada árbol visto a unos metros, para juzgar corteza y hojas.
"""

import math
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))

import render_fase1 as r1  # noqa: E402


def _luces(cmds):
    suelo = cmds.polyPlane(width=200000, height=200000, subdivisionsX=1, subdivisionsY=1, name="suelo")[0]
    tierra = cmds.shadingNode("standardSurface", asShader=True, name="tierra")
    cmds.setAttr(tierra + ".baseColor", 0.22, 0.2, 0.17, type="double3")
    cmds.setAttr(tierra + ".specular", 0.0)  # tierra seca: sin reflejos
    cmds.select(suelo)
    cmds.hyperShade(assign=tierra)
    cielo = cmds.shadingNode("aiSkyDomeLight", asLight=True, name="cielo")
    cmds.setAttr(cmds.listRelatives(cielo, shapes=True)[0] + ".color", 0.8, 0.88, 1.0, type="double3")
    sol = cmds.listRelatives(cmds.directionalLight(name="solShape", intensity=2.2), parent=True)[0]
    cmds.setAttr(sol + ".rotate", -35, 35, 0, type="double3")
    cmds.setAttr(cmds.listRelatives(cielo, shapes=True)[0] + ".intensity", 0.6)


def main(carpeta, *opciones):
    carpeta = os.path.abspath(carpeta)
    cmds = r1._iniciar()
    from arboles import construir_maya as cm
    from arboles import ejemplos, follaje
    os.makedirs(carpeta, exist_ok=True)
    cmds.file(new=True, force=True)
    cm.preparar()
    _luces(cmds)
    r1._ajustes(cmds)
    informe = []
    nombres = [p for p in ejemplos.PLANTILLAS if p != "vacio"]
    # En tres filas al tresbolillo, de delante (los bajos) a atrás (los altos)
    orden = sorted(nombres, key=lambda p: ejemplos.crear(p).calcular().tronco.guia.largo)
    sitios = {}
    for i, plantilla in enumerate(orden):
        fila, columna = divmod(i, 3)
        sitios[plantilla] = ((columna - 1) * 1700.0 + (fila % 2) * 600.0 - 300.0, -fila * 2000.0)
    for plantilla in nombres:
        arbol = ejemplos.crear(plantilla)
        cm.preparar(arbol)  # materiales con texturas de la especie
        x, z = sitios[plantilla]
        cm.crear(arbol, "medio", "catalogo_" + plantilla, posicion=(x, 0.0, z))
        informe.append("{}: {} triángulos ({})".format(plantilla, arbol.triangulos("medio"), arbol.semaforo()[0]))
    r1._camara(cmds, (0, 1300, 5200), (0, 450, -2000))
    informe.append("catálogo: " + r1._render(cmds, os.path.join(carpeta, "catalogo")))
    if "--cerca" in opciones:
        informe += _cerca(cmds, cm, nombres, carpeta)

    # los grupos de hojas, de cerca, en una fila a 2 m del suelo
    for g in cmds.ls("catalogo_*", assemblies=True):
        cmds.delete(g)
    tipos = list(follaje.TIPOS)
    for i, tipo in enumerate(tipos):
        x = (i - (len(tipos) - 1) / 2.0) * 70.0
        malla = follaje.combinar(tipo, "alto", [(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, 200.0, 0, 1)],
                                 "hojas_" + tipo)
        grupo = om_crear(cm, malla, "catalogo_hojas_" + tipo)
        informe.append("{}: {} triángulos por grupo".format(tipo, malla.triangulos))
        del grupo
    r1._camara(cmds, (0, 280, 760), (0, 225, 0))
    informe.append("hojas: " + r1._render(cmds, os.path.join(carpeta, "catalogo_hojas")))
    print("\n".join(informe))
    sys.stdout.flush()


def _cerca(cmds, cm, nombres, carpeta):
    """Cada árbol a unos metros, solo: el tronco abajo y la copa encima."""
    informe = []
    grupos = {p: cmds.ls("catalogo_" + p, assemblies=True, long=True)[0] for p in nombres}
    for plantilla in nombres:
        for otra, g in grupos.items():
            cmds.setAttr(g + ".visibility", otra == plantilla)
        caja = cmds.exactWorldBoundingBox(grupos[plantilla])
        x, z = (caja[0] + caja[3]) / 2.0, (caja[2] + caja[5]) / 2.0
        alto, ancho = caja[4] - caja[1], max(caja[3] - caja[0], caja[5] - caja[2])
        # Que quepa entero: 45° en horizontal y unos 26° en vertical (16:9), con un 10 % de margen.
        distancia = max(450.0, alto * 0.55 / math.tan(math.radians(13.1)), ancho * 0.55 / math.tan(math.radians(22.5)))
        r1._camara(cmds, (x + distancia * 0.3, alto * 0.35, z + distancia), (x, alto * 0.5, z))
        informe.append("cerca {}: {}".format(plantilla, r1._render(cmds, os.path.join(carpeta, "cerca_" + plantilla))))
    for g in grupos.values():
        cmds.setAttr(g + ".visibility", True)
    return informe


def om_crear(cm, malla, nombre):
    """Crea la malla suelta con el material de hoja."""
    import maya.api.OpenMaya as om
    transform = om.MFnDagNode().create("transform", nombre)
    forma = cm._crear_malla(malla, transform, nombre)
    cm._asignar(forma, cm.grupo_de(cm.HOJA))
    return transform


if __name__ == "__main__":
    main(*sys.argv[1:])
    os._exit(0)
