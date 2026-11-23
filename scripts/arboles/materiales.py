"""Materiales clay de Árboles.

Usa ``standardSurface``, que viene con Maya, se ve en el visor y Arnold lo
renderiza sin cargar nada más. Corteza y hoja van en materiales separados
para poder asignarles texturas por especie más adelante.
"""

from maya import cmds

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
