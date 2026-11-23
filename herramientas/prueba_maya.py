"""Prueba de las fases 0 y 1 dentro de Maya, sin interfaz (herramienta de desarrollo).

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

    # Fase 1: módulos, Generar y UVs
    import time
    from arboles import construir_maya, ejemplos
    inicio = time.time()
    grupo = construir_maya.crear(ejemplos.copa_redonda())
    print("  (árbol denso en {:.2f} s)".format(time.time() - inicio))
    mallas = cmds.listRelatives(grupo, children=True, type="transform") or []
    comprobar(len(mallas) == 22, "el árbol de ejemplo tiene 22 mallas (tronco y ramas)")
    denso = construir_maya.triangulos(grupo)
    esperado = ejemplos.copa_redonda().triangulos("denso")
    comprobar(denso == esperado, "triángulos en Maya iguales a los calculados ({})".format(denso))
    uvs = cmds.polyEvaluate(mallas[0], uvcoord=True)
    comprobar(uvs > 0, "el tronco tiene UVs ({})".format(uvs))
    caja_denso = cmds.polyEvaluate(mallas[0], boundingBox2d=True)
    comprobar(cmds.getAttr(grupo + ".arbolesNivel") == "denso", "nivel denso anotado")
    cmds.select(mallas[3])
    comprobar(construir_maya.grupos_seleccionados() == cmds.ls(grupo, long=True),
              "seleccionar una rama encuentra su árbol")
    inicio = time.time()
    construir_maya.generar(grupo, "medio")
    print("  (Generar medio en {:.2f} s)".format(time.time() - inicio))
    medio = construir_maya.triangulos(grupo)
    comprobar(medio < denso / 5.0, "Generar medio reduce triángulos ({} → {})".format(denso, medio))
    mallas = cmds.listRelatives(grupo, children=True, type="transform") or []
    caja_medio = cmds.polyEvaluate(mallas[0], boundingBox2d=True)
    comprobar(all(abs(a - b) < 1e-4 for par_a, par_b in zip(caja_denso, caja_medio)
                  for a, b in zip(par_a, par_b)),
              "el rango de UVs del tronco es el mismo en denso y medio")
    sg = creados["arboles_clay_corteza"][1]
    forma = cmds.listRelatives(mallas[0], shapes=True)[0]
    comprobar(sg in (cmds.listConnections(forma, type="shadingEngine") or []), "corteza clay tras Generar")
    comprobar(construir_maya.arbol_de(grupo).a_dict() == ejemplos.copa_redonda().a_dict(),
              "la receta guardada en el grupo se recupera igual")
    construir_maya.textura_cuadros(True)
    comprobar(cmds.isConnected("arboles_cuadros.outColor", "arboles_clay_corteza.baseColor"),
              "textura de cuadros conectada")
    construir_maya.textura_cuadros(False)
    comprobar(not cmds.listConnections("arboles_clay_corteza.baseColor", source=True, destination=False),
              "textura de cuadros quitada")
    for nivel in ("alto", "bajo", "denso"):
        construir_maya.generar(grupo, nivel)
    comprobar(construir_maya.triangulos(grupo) == denso, "volver a denso recupera la malla original")
    archivo = os.path.join(tmp, "arbol.ma")
    cmds.file(rename=archivo)
    cmds.file(save=True, type="mayaAscii", force=True)
    cmds.file(archivo, open=True, force=True)
    comprobar(construir_maya.es_arbol(grupo), "la receta sobrevive a guardar y abrir la escena")

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
