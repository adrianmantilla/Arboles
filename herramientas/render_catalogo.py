"""Render con Arnold del catálogo: todas las plantillas en fila (herramienta de desarrollo, fase 4).

    mayapy herramientas/render_catalogo.py /ruta/de/salida

Deja catalogo.png (las plantillas en frondosidad normal, calidad media) y
catalogo_hojas.png (un grupo de cada tipo de hoja, de cerca).
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))

import render_fase1 as r1  # noqa: E402


def _luces(cmds):
    from arboles import materiales
    suelo = cmds.polyPlane(width=20000, height=20000, subdivisionsX=1, subdivisionsY=1, name="suelo")[0]
    materiales.asignar(suelo, "arboles_clay_hoja")
    cielo = cmds.shadingNode("aiSkyDomeLight", asLight=True, name="cielo")
    cmds.setAttr(cmds.listRelatives(cielo, shapes=True)[0] + ".color", 0.8, 0.88, 1.0, type="double3")
    sol = cmds.listRelatives(cmds.directionalLight(name="solShape", intensity=2.2), parent=True)[0]
    cmds.setAttr(sol + ".rotate", -40, 35, 0, type="double3")


def main(carpeta):
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
    paso = 900.0
    for i, plantilla in enumerate(nombres):
        arbol = ejemplos.crear(plantilla)
        x = (i - (len(nombres) - 1) / 2.0) * paso
        cm.crear(arbol, "medio", "catalogo_" + plantilla, posicion=(x, 0.0, 0.0))
        informe.append("{}: {} triángulos ({})".format(plantilla, arbol.triangulos("medio"), arbol.semaforo()[0]))
    ancho = paso * len(nombres)
    r1._camara(cmds, (0, 600, ancho * 1.3), (0, 380, 0))
    informe.append("catálogo: " + r1._render(cmds, os.path.join(carpeta, "catalogo")))

    # los grupos de hojas, de cerca, en una fila a 2 m del suelo
    for g in cmds.ls("catalogo_*", assemblies=True):
        cmds.delete(g)
    tipos = list(follaje.TIPOS)
    for i, tipo in enumerate(tipos):
        x = (i - (len(tipos) - 1) / 2.0) * 90.0
        malla = follaje.combinar(tipo, "alto", [(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, 200.0, 0, 1)],
                                 "hojas_" + tipo)
        grupo = om_crear(cm, malla, "catalogo_hojas_" + tipo)
        informe.append("{}: {} triángulos por grupo".format(tipo, malla.triangulos))
        del grupo
    r1._camara(cmds, (0, 260, 620), (0, 225, 0))
    informe.append("hojas: " + r1._render(cmds, os.path.join(carpeta, "catalogo_hojas")))
    print("\n".join(informe))
    sys.stdout.flush()


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
