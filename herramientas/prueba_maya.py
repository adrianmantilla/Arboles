"""Prueba de la fase 0 dentro de Maya, sin interfaz (herramienta de desarrollo).

Desde la terminal, con el mayapy de cada versión:

    /Applications/Autodesk/maya2027/Maya.app/Contents/bin/mayapy herramientas/prueba_maya.py
    "C:\\Program Files\\Autodesk\\Maya2027\\bin\\mayapy.exe" herramientas\\prueba_maya.py

No toca tus preferencias de Maya: usa una carpeta temporal para los ajustes y
la biblioteca. Termina con «RESULTADO: OK» o con la lista de fallos.
"""

import os
import sys
import tempfile
import traceback

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

fallos = []


def comprobar(condicion, texto):
    print(("  ok    " if condicion else "  FALLO ") + texto)
    if not condicion:
        fallos.append(texto)


def main():
    import maya.standalone
    maya.standalone.initialize(name="python")
    from maya import cmds

    print("Maya", cmds.about(version=True), "-", cmds.about(operatingSystem=True))
    tmp = tempfile.mkdtemp(prefix="arboles_prueba_")

    # Plugin
    ruta_plugin = os.path.join(RAIZ, "plug-ins", "arboles_plugin.py")
    cmds.loadPlugin(ruta_plugin)
    comprobar(cmds.pluginInfo("arboles_plugin", query=True, loaded=True), "el plugin se carga")

    # Ajustes y biblioteca en carpeta temporal
    from arboles import ajustes as aj, interfaz_maya
    interfaz_maya.carpeta_preferencias = lambda: os.path.join(tmp, "prefs")
    comprobar(interfaz_maya.cargar_ajustes().primer_uso(), "primer uso detectado")
    ruta = interfaz_maya.cargar_ajustes().fijar_biblioteca(os.path.join(tmp, "Documents", "Arboles"))
    comprobar(aj.se_puede_escribir(ruta), "biblioteca creada y escribible")
    comprobar(interfaz_maya.carpeta_biblioteca() == ruta, "la carpeta se recuerda")

    # Materiales clay
    from arboles import materiales
    creados = materiales.crear_todos()
    otra_vez = materiales.crear_todos()
    comprobar(creados == otra_vez, "crear materiales dos veces no duplica")
    for nombre, (mat, grupo) in creados.items():
        comprobar(cmds.nodeType(mat) == "standardSurface", nombre + " es standardSurface")
        comprobar(cmds.nodeType(grupo) == "shadingEngine", nombre + " tiene grupo de sombreado")
    esfera = cmds.polySphere()[0]
    materiales.asignar(esfera, "arboles_clay_corteza")
    forma = cmds.listRelatives(esfera, shapes=True)[0]
    comprobar(creados["arboles_clay_corteza"][1] in (cmds.listConnections(forma, type="shadingEngine") or []),
              "asignar material a una malla")

    # Comprobación de la instalación (sin diálogo)
    _, lineas = interfaz_maya.comprobar(mostrar=False)
    comprobar(len(lineas) >= 4, "comprobar instalación devuelve informe")

    cmds.unloadPlugin("arboles_plugin")
    comprobar(not cmds.pluginInfo("arboles_plugin", query=True, loaded=True), "el plugin se descarga")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        fallos.append("excepción")
    print("RESULTADO: " + ("OK" if not fallos else "FALLOS: " + "; ".join(fallos)))
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0 if not fallos else 1)
