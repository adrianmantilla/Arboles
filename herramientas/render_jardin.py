"""Render con Arnold de un jardín plantado (herramienta de desarrollo, fase 3).

Planta copias ligadas de tres árboles de la biblioteca, renderiza el jardín,
cambia una rama del maestro de la copa redonda (más larga y sin hojas) y vuelve
a renderizar: todas sus copias deben cambiar a la vez.

    mayapy herramientas/render_jardin.py /ruta/de/salida
"""

import os
import random
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))

import render_fase1 as r1  # noqa: E402


def _plantar_jardin(cmds):
    from arboles import construir_maya, ejemplos, materiales, plantar
    cmds.file(new=True, force=True)
    construir_maya.preparar()
    suelo = cmds.polyPlane(width=8000, height=8000, subdivisionsX=1, subdivisionsY=1, name="suelo")[0]
    materiales.asignar(suelo, "arboles_clay_hoja")
    cielo = cmds.shadingNode("aiSkyDomeLight", asLight=True, name="cielo")
    cmds.setAttr(cmds.listRelatives(cielo, shapes=True)[0] + ".color", 0.8, 0.88, 1.0, type="double3")
    sol = cmds.listRelatives(cmds.directionalLight(name="solShape", intensity=2.2), parent=True)[0]
    cmds.setAttr(sol + ".rotate", -40, 35, 0, type="double3")
    forma_sol = cmds.listRelatives(sol, shapes=True)[0]
    if cmds.attributeQuery("aiAngle", node=forma_sol, exists=True):
        cmds.setAttr(forma_sol + ".aiAngle", 2.0)

    copa = ejemplos.crear("roble")
    copa.nombre = "Copa redonda"
    columnar = ejemplos.crear("cipres")
    columnar.nombre = "Columnar"
    arbusto = ejemplos.crear("arbusto")
    arbusto.nombre = "Arbusto"
    azar = random.Random(7)
    sitios = [(copa, (-1400, -900)), (copa, (0, -1100)), (copa, (1400, -800)), (copa, (-700, 300)),
              (copa, (800, 400)), (columnar, (-2000, 200)), (columnar, (2100, 100)),
              (columnar, (100, -2200)), (arbusto, (-300, 1100)), (arbusto, (400, 1000)),
              (arbusto, (1500, 900)), (arbusto, (-1400, 1000))]
    for arbol, (x, z) in sitios:
        x += azar.uniform(-120, 120)
        z += azar.uniform(-120, 120)
        plantar.plantar(arbol, (x, 0.0, z), "medio")
    return copa


def _rama_cambiada(copa):
    """La copa con su primera rama más larga y desnuda (para ver el cambio en todas las copias)."""
    nuevo = copa.copiar()
    rama = max(nuevo.hijos(nuevo.tronco.id), key=lambda m: -m.valores.get("posicion", 0.0))  # la más baja: lateral, se ve bien
    rama.fijar("longitud", rama.valores["longitud"] * 1.7)
    for id_ in [rama.id] + nuevo.descendientes(rama.id):
        nuevo.modulos[id_].fijar("densidad", 0.0)
    return nuevo


def main(carpeta):
    carpeta = os.path.abspath(carpeta)
    cmds = r1._iniciar()
    cmds.loadPlugin(os.path.join(RAIZ, "plug-ins", "arboles_plugin.py"))
    from arboles import plantar
    os.makedirs(carpeta, exist_ok=True)
    copa = _plantar_jardin(cmds)
    r1._ajustes(cmds)
    n, tri = plantar.informe()
    informe = ["jardín: {} copias, {} triángulos".format(n, tri)]
    r1._camara(cmds, (0, 1500, 5200), (0, 250, -300))
    informe.append("antes: " + r1._render(cmds, os.path.join(carpeta, "jardin_antes")))
    informe.append("maestros actualizados: {}".format(plantar.actualizar_maestros(_rama_cambiada(copa))))
    informe.append("después: " + r1._render(cmds, os.path.join(carpeta, "jardin_despues")))
    escena = os.path.join(carpeta, "jardin.ma")
    cmds.file(rename=escena)
    cmds.file(save=True, type="mayaAscii", force=True)
    informe.append("escena: " + escena)
    print("\n".join(informe))
    sys.stdout.flush()


if __name__ == "__main__":
    main(*sys.argv[1:])
    os._exit(0)
