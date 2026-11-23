"""Plugin de Maya para Árboles.

Aparece en el Plug-in Manager como «arboles_plugin». Al cargarlo crea el menú
Árboles en la barra de Maya; al descargarlo lo quita. El instalador lo marca
para que se cargue solo cada vez que se abre Maya.
"""

import maya.api.OpenMaya as om
from maya import cmds


def maya_useNewAPI():
    pass


def initializePlugin(objeto):
    import arboles
    plugin = om.MFnPlugin(objeto, "Árboles", arboles.__version__, "Any")
    try:
        from arboles import interfaz_maya
        cmds.evalDeferred(interfaz_maya.iniciar, lowestPriority=True)
    except Exception as error:
        cmds.warning("Árboles no se pudo cargar: {}".format(error))
    return plugin


def uninitializePlugin(objeto):
    try:
        from arboles import interfaz_maya
        interfaz_maya.quitar_menu()
    except Exception:
        pass
