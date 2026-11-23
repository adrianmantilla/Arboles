"""Construye en Maya las mallas de un Arbol y las vuelve a generar a otro nivel.

Cada árbol es un grupo con la receta guardada en el atributo «arbolesReceta».
Generar lee esa receta y reconstruye las mallas del grupo con menos
divisiones: las UVs se calculan igual, así que los materiales siguen encajando.
"""

import maya.api.OpenMaya as om
from maya import cmds

from arboles import materiales
from arboles.arbol import Arbol
from arboles.modulos import NIVELES

ATRIBUTO_RECETA = "arbolesReceta"
ATRIBUTO_NIVEL = "arbolesNivel"
CUADROS = "arboles_cuadros"


def _crear_malla(datos, padre):
    puntos = om.MPointArray([om.MPoint(*p) for p in datos.vertices])
    malla = om.MFnMesh()
    transformada = malla.create(puntos, datos.conteos, datos.conexiones, datos.us, datos.vs)
    malla.assignUVs(datos.conteos, datos.uv_ids)
    nombre = cmds.rename(om.MFnDagNode(transformada).fullPathName(), datos.nombre)
    cmds.polySoftEdge(nombre, angle=180, constructionHistory=False)
    return cmds.parent(nombre, padre)[0]


def _mallas_del_grupo(grupo):
    return cmds.listRelatives(grupo, children=True, type="transform", fullPath=True) or []


def _construir_en(grupo, arbol, nivel):
    for hijo in _mallas_del_grupo(grupo):
        cmds.delete(hijo)
    mallas = [_crear_malla(datos, grupo) for datos in arbol.mallas(nivel)]
    if mallas:
        materiales.asignar(mallas, "arboles_clay_corteza")
    cmds.setAttr(grupo + "." + ATRIBUTO_NIVEL, nivel, type="string")
    return mallas


def _sin_deshacer(funcion, *args):
    """Las mallas se crean con la API de Maya, que no entra en el deshacer de cmds.

    Para no dejar un Ctrl+Z a medias, la construcción no se registra en el
    deshacer. En la fase 2 pasará a ser un comando del plugin con deshacer propio.
    """
    estado = cmds.undoInfo(query=True, stateWithoutFlush=True)
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        return funcion(*args)
    finally:
        cmds.undoInfo(stateWithoutFlush=estado)


def crear(arbol, nivel="denso", nombre=None):
    """Crea un grupo nuevo con el árbol y devuelve su nombre."""
    return _sin_deshacer(_crear, arbol, nivel, nombre)


def _crear(arbol, nivel, nombre):
    grupo = cmds.group(empty=True, name=(nombre or arbol.nombre) + "_grp")
    cmds.addAttr(grupo, longName=ATRIBUTO_RECETA, dataType="string")
    cmds.addAttr(grupo, longName=ATRIBUTO_NIVEL, dataType="string")
    cmds.setAttr(grupo + "." + ATRIBUTO_RECETA, arbol.a_json(), type="string")
    _construir_en(grupo, arbol, nivel)
    return grupo


def es_arbol(nodo):
    return cmds.objExists(nodo) and cmds.attributeQuery(ATRIBUTO_RECETA, node=nodo, exists=True)


def arbol_de(grupo):
    return Arbol.de_json(cmds.getAttr(grupo + "." + ATRIBUTO_RECETA))


def grupos_seleccionados():
    """Grupos de árbol en la selección (vale seleccionar una de sus mallas)."""
    encontrados = []
    for nodo in cmds.ls(selection=True, long=True) or []:
        while nodo and not es_arbol(nodo):
            padres = cmds.listRelatives(nodo, parent=True, fullPath=True)
            nodo = padres[0] if padres else None
        if nodo and nodo not in encontrados:
            encontrados.append(nodo)
    return encontrados


def generar(grupo, nivel):
    """Reconstruye el árbol del grupo al nivel indicado (alto, medio, bajo o denso)."""
    if nivel not in NIVELES:
        raise ValueError("nivel desconocido: {}".format(nivel))
    return _sin_deshacer(_construir_en, grupo, arbol_de(grupo), nivel)


def triangulos(grupo):
    mallas = _mallas_del_grupo(grupo)
    return sum(cmds.polyEvaluate(m, triangle=True) for m in mallas) if mallas else 0


def textura_cuadros(activar=True, repeticiones=8):
    """Pone (o quita) una textura de cuadros en la corteza para revisar las UVs."""
    material, _ = materiales.crear_material("arboles_clay_corteza")
    destino = material + ".baseColor"
    if activar:
        if not cmds.objExists(CUADROS):
            cmds.shadingNode("checker", asTexture=True, name=CUADROS)
            colocacion = cmds.shadingNode("place2dTexture", asUtility=True, name=CUADROS + "_place")
            cmds.connectAttr(colocacion + ".outUV", CUADROS + ".uvCoord")
            cmds.connectAttr(colocacion + ".outUvFilterSize", CUADROS + ".uvFilterSize")
        colocacion = CUADROS + "_place"
        cmds.setAttr(colocacion + ".repeatU", repeticiones)
        cmds.setAttr(colocacion + ".repeatV", repeticiones)
        cmds.connectAttr(CUADROS + ".outColor", destino, force=True)
    else:
        for origen in cmds.listConnections(destino, plugs=True, source=True, destination=False) or []:
            cmds.disconnectAttr(origen, destino)
        color = materiales.CLAY["arboles_clay_corteza"][0]
        cmds.setAttr(destino, *color, type="double3")
    return activar
