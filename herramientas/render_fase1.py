"""Render con Arnold del árbol de ejemplo (herramienta de desarrollo).

Pone dos copias del árbol de ejemplo con la textura de cuadros en la corteza:
a la izquierda la malla densa del editor y a la derecha la versión ligera
(«bajo»). Si las UVs son buenas, los cuadros son iguales en las dos.
Renderiza también una vista en clay sin cuadros.

    mayapy herramientas/render_fase1.py /ruta/de/salida [prefijo]
"""

import glob
import os
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
ANCHO, ALTO = 1280, 720


def _iniciar():
    import maya.standalone
    maya.standalone.initialize(name="python")
    from maya import cmds
    if not cmds.pluginInfo("mtoa", query=True, loaded=True):
        cmds.loadPlugin("mtoa")
    return cmds


def _escena(cmds):
    from arboles import construir_maya, ejemplos, materiales
    cmds.file(new=True, force=True)
    izquierda = construir_maya.crear(ejemplos.copa_redonda(), "denso", "ejemplo_denso")
    derecha = construir_maya.crear(ejemplos.copa_redonda(), "bajo", "ejemplo_bajo")
    cmds.move(-380, 0, 0, izquierda)
    cmds.move(380, 0, 0, derecha)
    suelo = cmds.polyPlane(width=6000, height=6000, subdivisionsX=1, subdivisionsY=1, name="suelo")[0]
    materiales.asignar(suelo, "arboles_clay_hoja")
    cielo = cmds.shadingNode("aiSkyDomeLight", asLight=True, name="cielo")
    forma_cielo = cmds.listRelatives(cielo, shapes=True)[0]
    cmds.setAttr(forma_cielo + ".color", 0.8, 0.88, 1.0, type="double3")
    sol = cmds.listRelatives(cmds.directionalLight(name="solShape", intensity=2.2), parent=True)[0]
    cmds.setAttr(sol + ".rotate", -40, 35, 0, type="double3")
    forma_sol = cmds.listRelatives(sol, shapes=True)[0]
    if cmds.attributeQuery("aiAngle", node=forma_sol, exists=True):
        cmds.setAttr(forma_sol + ".aiAngle", 2.0)
    return izquierda, derecha


def _ajustes(cmds):
    import mtoa.core
    mtoa.core.createOptions()
    cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
    for atributo, valor in (("AASamples", 4), ("GIDiffuseSamples", 2), ("abortOnLicenseFail", 0)):
        if cmds.attributeQuery(atributo, node="defaultArnoldRenderOptions", exists=True):
            cmds.setAttr("defaultArnoldRenderOptions." + atributo, valor)
    cmds.setAttr("defaultArnoldDriver.ai_translator", "png", type="string")
    for ajuste in (dict(outputTransformEnabled=True), dict(outputUseViewTransform=True)):
        try:
            cmds.colorManagementPrefs(edit=True, **ajuste)
        except (RuntimeError, TypeError):
            pass
    cmds.setAttr("defaultResolution.width", ANCHO)
    cmds.setAttr("defaultResolution.height", ALTO)
    cmds.setAttr("defaultResolution.deviceAspectRatio", ANCHO / float(ALTO))


def _camara(cmds, ojo, mira):
    if not cmds.objExists("render_cam"):
        cmds.rename(cmds.camera()[0], "render_cam")
    cmds.viewPlace("render_cam", eye=ojo, lookAt=mira, perspective=True)
    cmds.camera("render_cam", edit=True, horizontalFieldOfView=45, farClipPlane=1e6)
    for camara in cmds.ls(type="camera"):
        cmds.setAttr(camara + ".renderable", 0)
    cmds.setAttr(cmds.listRelatives("render_cam", shapes=True)[0] + ".renderable", 1)
    return "render_cam"


def _render(cmds, base):
    cmds.setAttr("defaultRenderGlobals.imageFilePrefix", base, type="string")
    inicio = time.time()
    cmds.arnoldRender(width=ANCHO, height=ALTO, camera="render_cam", batch=True)
    raiz = cmds.workspace(query=True, rootDirectory=True) or ""
    hechas = glob.glob(base + "*.png") + [
        r for r in glob.glob(os.path.join(raiz, "images", "**", "*.png"), recursive=True)
        if os.path.getmtime(r) >= inicio]
    return "{:.1f} s, {}".format(time.time() - inicio, sorted(hechas, key=os.path.getmtime)[-1] if hechas else "SIN IMAGEN")


def main(carpeta, prefijo="fase1"):
    cmds = _iniciar()
    from arboles import construir_maya
    os.makedirs(carpeta, exist_ok=True)
    izquierda, derecha = _escena(cmds)
    _ajustes(cmds)
    informe = ["denso: {} triángulos".format(construir_maya.triangulos(izquierda)),
               "bajo: {} triángulos".format(construir_maya.triangulos(derecha))]
    _camara(cmds, (0, 330, 1900), (0, 290, 0))
    construir_maya.textura_cuadros(True, repeticiones=4)
    informe.append("cuadros: " + _render(cmds, os.path.join(carpeta, prefijo + "_cuadros")))
    construir_maya.textura_cuadros(False)
    informe.append("clay: " + _render(cmds, os.path.join(carpeta, prefijo + "_clay")))
    _camara(cmds, (-380, 120, 380), (-380, 110, 0))
    construir_maya.textura_cuadros(True, repeticiones=4)
    informe.append("base cuadros: " + _render(cmds, os.path.join(carpeta, prefijo + "_base_cuadros")))
    escena = os.path.join(carpeta, prefijo + ".ma")
    cmds.file(rename=escena)
    cmds.file(save=True, type="mayaAscii", force=True)
    informe.append("escena: " + escena)
    print("\n".join(informe))
    sys.stdout.flush()


if __name__ == "__main__":
    main(*sys.argv[1:])
    os._exit(0)
