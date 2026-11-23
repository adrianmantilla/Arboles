"""Abre el editor en Maya con interfaz, guarda capturas y cierra Maya (herramienta de desarrollo).

    MAYA_APP_DIR=/tmp/maya_prueba ARBOLES_SALIDA=/tmp/capturas \\
      /Applications/Autodesk/maya2027/Maya.app/Contents/bin/maya \\
      -command "python(\\"exec(open('herramientas/captura_editor.py').read())\\")"

Usa una carpeta de preferencias y una biblioteca temporales dentro de ARBOLES_SALIDA.
Deja ventana.png, visor.png, miniatura.png, plantar.png y jardin.png en ARBOLES_SALIDA.
"""

import os
import sys
import traceback

from maya import cmds

_RAIZ = os.environ.get("ARBOLES_RAIZ") or os.getcwd()
_SALIDA = os.environ.get("ARBOLES_SALIDA") or os.path.join(_RAIZ, "capturas")


def _capturar_y_salir():
    try:
        os.makedirs(_SALIDA, exist_ok=True)
        sys.path.insert(0, os.path.join(_RAIZ, "scripts"))
        from arboles import interfaz_maya
        interfaz_maya.carpeta_preferencias = lambda: os.path.join(_SALIDA, "prefs")
        interfaz_maya.cargar_ajustes().fijar_biblioteca(os.path.join(_SALIDA, "biblioteca"))
        cmds.loadPlugin(os.path.join(_RAIZ, "plug-ins", "arboles_plugin.py"))
        from arboles import editor_ui
        try:
            from PySide6 import QtWidgets
        except ImportError:
            from PySide2 import QtWidgets
        w = editor_ui.mostrar()
        w.move(40, 40)
        ramas = [i for i in w.editor.arbol.modulos if i != w.editor.arbol.tronco.id]
        w._seleccionar_ids(ramas[2:3])
        w.figura.setChecked(True)
        w.tiradores.setChecked(True)
        QtWidgets.QApplication.processEvents()
        cmds.viewFit("persp", w.editor.grupo, fitFactor=0.8)
        cmds.refresh(force=True)
        QtWidgets.QApplication.processEvents()
        w.grab().save(os.path.join(_SALIDA, "ventana.png"))
        print("ARBOLES_CAPTURA ventana")
        cmds.select(clear=True)
        panel = cmds.getPanel(withFocus=True)
        if cmds.getPanel(typeOf=panel) != "modelPanel":
            panel = cmds.getPanel(type="modelPanel")[0]
        cmds.modelEditor(panel, edit=True, displayAppearance="smoothShaded", grid=True)
        cmds.playblast(frame=[1], format="image", compression="png", viewer=False,
                       completeFilename=os.path.join(_SALIDA, "visor.png"), widthHeight=(1200, 900),
                       percent=100, showOrnaments=False, forceOverwrite=True)
        print("ARBOLES_CAPTURA visor")
        w.tiradores.setChecked(False)
        w.figura.setChecked(False)
        w.editor.miniatura(os.path.join(_SALIDA, "miniatura.png"))
        print("ARBOLES_CAPTURA miniatura")
        # Fase 3: guardar, plantar un jardín y capturar el panel y el visor
        from arboles import plantar, plantar_ui
        from arboles.biblioteca import Biblioteca
        bib = Biblioteca(os.path.join(_SALIDA, "biblioteca"))
        w.editor.arbol.nombre = "Copa redonda"
        bib.guardar(w.editor.arbol)
        w.editor.miniatura(bib.ruta_miniatura("Copa redonda"))
        w.close()
        cmds.setAttr(w.editor.grupo + ".visibility", 0)
        if cmds.objExists("arboles_figura_humana"):
            cmds.setAttr("arboles_figura_humana.visibility", 0)
        suelo = cmds.polyPlane(width=6000, height=6000, subdivisionsX=1, subdivisionsY=1, name="suelo")[0]
        arbol = bib.cargar("Copa_redonda")
        for i in range(7):
            x, z = (i % 4) * 700.0 - 1000.0, (i // 4) * 800.0 - 400.0
            plantar.plantar(arbol, plantar.punto_en_suelo((x, 2000.0, z), (0.0, -1.0, 0.0)))
        p = plantar_ui.mostrar()
        p.move(40, 40)
        QtWidgets.QApplication.processEvents()
        p.grab().save(os.path.join(_SALIDA, "plantar.png"))
        cmds.select(clear=True)
        cmds.viewFit("persp", plantar.plantados() + [suelo], fitFactor=0.9)
        cmds.refresh(force=True)
        cmds.playblast(frame=[1], format="image", compression="png", viewer=False,
                       completeFilename=os.path.join(_SALIDA, "jardin.png"), widthHeight=(1200, 800),
                       percent=100, showOrnaments=False, forceOverwrite=True)
        print("ARBOLES_CAPTURA jardin")
        print("ARBOLES_CAPTURA OK")
    except Exception:
        traceback.print_exc()
        print("ARBOLES_CAPTURA FALLO")
    finally:
        sys.stdout.flush()
        cmds.quit(force=True)


cmds.evalDeferred(_capturar_y_salir, lowestPriority=True)
