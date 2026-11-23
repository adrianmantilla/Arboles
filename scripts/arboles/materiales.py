"""Materiales de Árboles: clay y, si están instaladas, texturas por especie.

Usa ``standardSurface``, que viene con Maya, se ve en el visor y Arnold lo
renderiza sin cargar nada más. Corteza y hoja van en materiales separados.
Los materiales con texturas se llaman ``arboles_<juego>_corteza`` y
``arboles_<juego>_hoja`` y leen las imágenes de ``texturas/<juego>/<resolución>``.
"""

from maya import cmds

from arboles import texturas as tx

# nombre: (color base, rugosidad, intensidad especular, transmisión)
CLAY = {
    "arboles_clay_corteza": ((0.58, 0.55, 0.52), 0.6, 0.3, 0.0),
    "arboles_clay_hoja": ((0.66, 0.66, 0.62), 0.5, 0.35, 0.15),
}


def _grupo(material):
    conexiones = cmds.listConnections(material + ".outColor", type="shadingEngine") or []
    if conexiones:
        return conexiones[0]
    grupo = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=material + "SG")
    cmds.connectAttr(material + ".outColor", grupo + ".surfaceShader", force=True)
    return grupo


def crear_material(nombre):
    """Devuelve (material, grupo de sombreado); lo crea si no existe."""
    if cmds.objExists(nombre):
        return nombre, _grupo(nombre)
    color, rugosidad, especular, transmision = CLAY[nombre]
    material = cmds.shadingNode("standardSurface", asShader=True, name=nombre)
    cmds.setAttr(material + ".base", 1.0)
    cmds.setAttr(material + ".baseColor", *color, type="double3")
    cmds.setAttr(material + ".specular", especular)
    cmds.setAttr(material + ".specularRoughness", rugosidad)
    if transmision:
        # Las hojas dejan pasar algo de luz, como en Trepadora.
        cmds.setAttr(material + ".thinWalled", 1)
        cmds.setAttr(material + ".subsurface", transmision)
        cmds.setAttr(material + ".subsurfaceColor", *color, type="double3")
    return material, _grupo(material)


def crear_todos():
    return {nombre: crear_material(nombre) for nombre in CLAY}


def asignar(objetos, nombre):
    _, grupo = crear_material(nombre)
    cmds.sets(objetos, edit=True, forceElement=grupo)


# --- texturas por especie ---------------------------------------------------------

def nombre_material(juego, parte):
    """Material que usa ``parte`` (corteza u hoja) de un árbol con ese juego de texturas."""
    if not tx.existe(juego):
        return "arboles_clay_" + parte
    return "arboles_{}_{}".format(juego, parte)


def _archivo(nombre, ruta, color):
    nodo = cmds.shadingNode("file", asTexture=True, isColorManaged=True, name=nombre)
    colocacion = cmds.shadingNode("place2dTexture", asUtility=True, name=nombre + "_place")
    for a, b in (("outUV", "uvCoord"), ("outUvFilterSize", "uvFilterSize")):
        cmds.connectAttr(colocacion + "." + a, nodo + "." + b)
    cmds.setAttr(nodo + ".fileTextureName", ruta, type="string")
    if not color:
        cmds.setAttr(nodo + ".colorSpace", "Raw", type="string")
        cmds.setAttr(nodo + ".ignoreColorSpaceFileRules", 1)
        cmds.setAttr(nodo + ".alphaIsLuminance", 1)
    return nodo


def crear_material_texturas(juego, parte, resolucion=tx.RESOLUCION_POR_DEFECTO):
    """(material, grupo) con las texturas de ``juego``; clay si el juego no está instalado."""
    nombre = nombre_material(juego, parte)
    if cmds.objExists(nombre):
        return nombre, _grupo(nombre)
    if not tx.existe(juego):
        return crear_material(nombre)
    clay = CLAY["arboles_clay_" + parte]
    material = cmds.shadingNode("standardSurface", asShader=True, name=nombre)
    cmds.setAttr(material + ".base", 1.0)
    cmds.setAttr(material + ".baseColor", *clay[0], type="double3")  # si falta la imagen de color
    cmds.setAttr(material + ".specular", clay[2])
    cmds.setAttr(material + ".specularRoughness", clay[1])
    if parte == "hoja":
        cmds.setAttr(material + ".thinWalled", 1)
        cmds.setAttr(material + ".subsurface", 0.25)
        cmds.setAttr(material + ".subsurfaceColor", *clay[0], type="double3")
    canales = tx.canales(juego, parte, resolucion)
    if "color" in canales:
        n = _archivo(nombre + "_color", canales["color"], True)
        cmds.connectAttr(n + ".outColor", material + ".baseColor")
        if parte == "hoja" and "translucidez" not in canales:
            cmds.connectAttr(n + ".outColor", material + ".subsurfaceColor")
    if "translucidez" in canales:
        n = _archivo(nombre + "_translucidez", canales["translucidez"], True)
        cmds.connectAttr(n + ".outColor", material + ".subsurfaceColor")
    if "rugosidad" in canales:
        n = _archivo(nombre + "_rugosidad", canales["rugosidad"], False)
        cmds.connectAttr(n + ".outAlpha", material + ".specularRoughness")
    if "normal" in canales:
        n = _archivo(nombre + "_normal", canales["normal"], False)
        relieve = cmds.shadingNode("bump2d", asUtility=True, name=nombre + "_relieve")
        cmds.setAttr(relieve + ".bumpInterp", 1)  # mapa de normales en espacio tangente
        cmds.connectAttr(n + ".outAlpha", relieve + ".bumpValue")
        cmds.connectAttr(relieve + ".outNormal", material + ".normalCamera")
        cmds.setAttr(n + ".alphaIsLuminance", 0)
    return material, _grupo(material)


def cambiar_resolucion(resolucion):
    """Vuelve a apuntar las texturas de los materiales de la escena a ``resolucion``."""
    cambiados = 0
    for nodo in cmds.ls("arboles_*_color", "arboles_*_normal", "arboles_*_rugosidad", "arboles_*_translucidez",
                        type="file") or []:
        partes = nodo.split("_")  # arboles, <juego…>, <parte>, <canal>
        juego, parte, canal = "_".join(partes[1:-2]), partes[-2], partes[-1]
        ruta = tx.ruta(juego, parte, canal, resolucion)
        if ruta:
            cmds.setAttr(nodo + ".fileTextureName", ruta, type="string")
            cambiados += 1
    return cambiados
