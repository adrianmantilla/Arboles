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
        # guardar otra vez con un cambio: la miniatura y el icono del panel deben cambiar
        import hashlib

        def _md5(ruta):
            with open(ruta, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()

        def _icono_panel():
            img = p.lista.item(0).icon().pixmap(64, 64).toImage()
            return bytes(img.constBits())[:img.sizeInBytes()] if hasattr(img, "sizeInBytes") else img.text()

        antes_md5, antes_icono = _md5(bib.ruta_miniatura("Copa redonda")), _icono_panel()
        cmds.setAttr(w.editor.grupo + ".visibility", 1)
        ramas = [m.id for m in w.editor.arbol.modulos.values() if m.tipo == "rama"]
        w.editor.fijar_valor(ramas, "densidad", 0.15)
        bib.guardar(w.editor.arbol)
        w.editor.miniatura(bib.ruta_miniatura("Copa redonda"))
        cmds.setAttr(w.editor.grupo + ".visibility", 0)
        plantar_ui.refrescar_si_abierto()
        QtWidgets.QApplication.processEvents()
        with open(os.path.join(_SALIDA, "miniatura_cambia.txt"), "w") as f:
            f.write("archivo cambia: {}\nicono cambia: {}\n".format(
                _md5(bib.ruta_miniatura("Copa redonda")) != antes_md5, _icono_panel() != antes_icono))
        p.grab().save(os.path.join(_SALIDA, "plantar_2.png"))
        cmds.select(clear=True)
        # encuadre explícito: viewFit no funciona bien con copias instanciadas
        x0, y0, z0, x1, y1, z1 = cmds.exactWorldBoundingBox(*plantar.plantados())
        cx, cz, alto = (x0 + x1) / 2.0, (z0 + z1) / 2.0, y1 - y0
        lado = max(x1 - x0, z1 - z0, alto)
        cmds.viewPlace("persp", eye=(cx, alto * 1.1, z1 + lado * 1.4), lookAt=(cx, alto * 0.4, cz),
                       perspective=True)
        panel = cmds.getPanel(withFocus=True)
        if cmds.getPanel(typeOf=panel) == "modelPanel":
            cmds.modelPanel(panel, edit=True, camera="persp")
        cmds.refresh(force=True)
        cmds.playblast(frame=[1], format="image", compression="png", viewer=False,
                       completeFilename=os.path.join(_SALIDA, "jardin.png"), widthHeight=(1200, 800),
                       percent=100, showOrnaments=False, forceOverwrite=True)
        print("ARBOLES_CAPTURA jardin")
        # el rayo del clic en el visor (lo usan Plantar con clic y Añadir rama con clic)
        from arboles import construir_maya as cm
        origen, direccion = cm.rayo_del_visor(600, 400)
        suelo_clic = plantar.punto_en_suelo(origen, direccion)
        with open(os.path.join(_SALIDA, "rayo.txt"), "w") as f:
            f.write("origen {}\ndireccion {}\nsuelo {}\n".format(origen, direccion, suelo_clic))
        print("ARBOLES_CAPTURA rayo")
        # fase 4: botón Ejemplos en una biblioteca aparte (miniaturas de todas las plantillas)
        bib_ejemplos = Biblioteca(os.path.join(_SALIDA, "biblioteca_ejemplos"))
        plantar.anadir_ejemplos(bib_ejemplos)
        print("ARBOLES_CAPTURA ejemplos")
        print("ARBOLES_CAPTURA OK")
    except Exception:
        traceback.print_exc()
        print("ARBOLES_CAPTURA FALLO")
    finally:
        sys.stdout.flush()
        cmds.quit(force=True)


cmds.evalDeferred(_capturar_y_salir, lowestPriority=True)
