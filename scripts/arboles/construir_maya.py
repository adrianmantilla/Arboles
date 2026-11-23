"""Construye en Maya las mallas y el follaje de un Arbol.

Todo se hace con la API de Maya (sin cmds) para que se pueda llamar desde el
deshacer del comando «arbolesAccion» del plugin. Los materiales se crean
antes, fuera del deshacer (``preparar()``).

Estructura de un árbol en la escena::

    <grupo>            atributos arbolesReceta (JSON) y arbolesNivel
      <id de módulo>   malla de tronco o rama, atributo arbolesModulo
      follaje          grupos de hojas: instancias de los prototipos
    arboles_prototipos (oculto)  un grupo de hojas por tipo y calidad
"""

import maya.api.OpenMaya as om
from maya import cmds

from arboles import follaje, materiales
from arboles.arbol import Arbol
from arboles.modulos import NIVELES

ATRIBUTO_RECETA = "arbolesReceta"
ATRIBUTO_NIVEL = "arbolesNivel"
ATRIBUTO_MODULO = "arbolesModulo"
ATRIBUTO_FOLLAJE = "arbolesFollaje"
PROTOTIPOS = "arboles_prototipos"
CUADROS = "arboles_cuadros"
CORTEZA = "arboles_clay_corteza"
HOJA = "arboles_clay_hoja"


# --- utilidades de la API -----------------------------------------------------

def _objeto(nombre):
    sel = om.MSelectionList()
    sel.add(nombre)
    return sel.getDependNode(0)


def _camino(nombre):
    sel = om.MSelectionList()
    sel.add(nombre)
    return sel.getDagPath(0)


def existe(nombre):
    try:
        _objeto(nombre)
        return True
    except (RuntimeError, ValueError):
        return False


def _transformada(nombre, padre=None):
    fn = om.MFnDagNode()
    obj = fn.create("transform", nombre, padre if padre is not None else om.MObject.kNullObj)
    return obj


def _atributo_texto(obj, nombre, valor):
    fn = om.MFnDependencyNode(obj)
    if not fn.hasAttribute(nombre):
        atributo = om.MFnTypedAttribute().create(nombre, nombre, om.MFnData.kString)
        fn.addAttribute(atributo)
    fn.findPlug(nombre, False).setString(valor)


def leer_texto(nombre_nodo, atributo):
    fn = om.MFnDependencyNode(_objeto(nombre_nodo))
    if not fn.hasAttribute(atributo):
        return None
    return fn.findPlug(atributo, False).asString()


def _soltar_instancias(obj):
    """Quita de ``obj`` y su descendencia las formas instanciadas (las hojas).

    Borrar un transform con MDagModifier borra también sus formas, aunque
    estén instanciadas en otros sitios: sin esto se perdería el prototipo y
    Maya acabaría con nodos inválidos (cuelgues y cierres).
    """
    pares = []
    pila = [obj]
    while pila:
        actual = pila.pop()
        fn = om.MFnDagNode(actual)
        for i in range(fn.childCount()):
            hijo = fn.child(i)
            if hijo.hasFn(om.MFn.kShape) and om.MFnDagNode(hijo).parentCount() > 1:
                pares.append((actual, hijo))
            elif hijo.hasFn(om.MFn.kTransform):
                pila.append(hijo)
    for padre, hijo in pares:
        om.MFnDagNode(padre).removeChild(hijo)


def _borrar(objetos):
    if not objetos:
        return
    for obj in objetos:
        _soltar_instancias(obj)
    mod = om.MDagModifier()
    for obj in objetos:
        mod.deleteNode(obj)
    mod.doIt()


def _hijos(obj):
    fn = om.MFnDagNode(obj)
    return [fn.child(i) for i in range(fn.childCount())]


def _nombre(obj):
    return om.MFnDagNode(obj).partialPathName()


def _asignar(obj_forma, grupo_sombreado):
    om.MFnSet(_objeto(grupo_sombreado)).addMember(obj_forma)


def grupo_de(material):
    """Grupo de sombreado (shadingEngine) de un material, con la API."""
    plug = om.MFnDependencyNode(_objeto(material)).findPlug("outColor", False)
    for destino in plug.connectedTo(False, True):
        if destino.node().hasFn(om.MFn.kShadingEngine):
            return om.MFnDependencyNode(destino.node()).name()
    raise RuntimeError("{} no tiene grupo de sombreado".format(material))


def _crear_malla(datos, padre, nombre):
    puntos = [om.MPoint(*p) for p in datos.vertices]
    fn = om.MFnMesh()
    forma = fn.create(puntos, datos.conteos, datos.conexiones, datos.us, datos.vs, padre)
    fn.assignUVs(datos.conteos, datos.uv_ids)
    aristas = list(range(fn.numEdges))
    fn.setEdgeSmoothings(aristas, [True] * len(aristas))
    fn.cleanupEdgeSmoothing()
    fn.updateSurface()
    om.MFnDependencyNode(forma).setName(nombre + "Shape")
    return forma


# --- preparación (fuera del deshacer) -----------------------------------------

def preparar():
    """Materiales y prototipos de hojas. Usa cmds: llamar antes de construir."""
    corteza = materiales.crear_material(CORTEZA)[1]
    hoja = materiales.crear_material(HOJA)[1]
    if not existe(PROTOTIPOS):
        grupo = _transformada(PROTOTIPOS)
        for tipo in follaje.TIPOS:
            for calidad in follaje.CALIDADES:
                datos = follaje.prototipo(tipo, calidad)
                t = _transformada(datos.nombre, grupo)
                _asignar(_crear_malla(datos, t, datos.nombre), hoja)
        cmds.setAttr(PROTOTIPOS + ".visibility", 0)
        cmds.setAttr(PROTOTIPOS + ".hiddenInOutliner", 1)
    return corteza, hoja


def _forma_prototipo(tipo, nivel):
    nombre = "{}_{}".format(tipo, follaje.calidad_de_nivel(nivel))
    camino = _camino(PROTOTIPOS + "|" + nombre)
    camino.extendToShape()
    return camino.node()


# --- construcción ---------------------------------------------------------------

def _construir_modulo(grupo, arbol, modulo, nivel, sg_corteza):
    from arboles import modulos as mod
    datos = mod.malla_tubo(modulo.guia, nivel, modulo.id, modulo.valores["torsion"], arbol.escala_textura)
    t = _transformada(modulo.id, grupo)
    _atributo_texto(t, ATRIBUTO_MODULO, modulo.id)
    _asignar(_crear_malla(datos, t, modulo.id), sg_corteza)
    return t


def _construir_follaje(contenedor, modulo, nivel):
    from arboles import follaje as fol
    matrices = fol.colocar(modulo)
    if not matrices:
        return None
    grupo = _transformada(modulo.id + "_hojas", contenedor)
    _atributo_texto(grupo, ATRIBUTO_MODULO, modulo.id)
    forma = _forma_prototipo(modulo.valores["follaje"], nivel)
    for i, m in enumerate(matrices):
        t = _transformada("{}_hoja{}".format(modulo.id, i), grupo)
        om.MFnTransform(t).setTransformation(om.MTransformationMatrix(om.MMatrix(m)))
        om.MFnDagNode(t).addChild(forma, om.MFnDagNode.kNextPos, True)  # instancia
    return grupo


def _contenedor_follaje(grupo, crear=True):
    for h in _hijos(grupo):
        if om.MFnDependencyNode(h).hasAttribute(ATRIBUTO_FOLLAJE):
            return h
    if not crear:
        return None
    contenedor = _transformada("follaje", grupo)
    _atributo_texto(contenedor, ATRIBUTO_FOLLAJE, "1")
    return contenedor


def _modulo_de(obj):
    fn = om.MFnDependencyNode(obj)
    return fn.findPlug(ATRIBUTO_MODULO, False).asString() if fn.hasAttribute(ATRIBUTO_MODULO) else None


def reconstruir(grupo, arbol, nivel, ids=None, guardar_receta=True):
    """(Re)construye en ``grupo`` los módulos ``ids`` (todos si es None) al ``nivel``.

    Quita las mallas y el follaje de módulos que ya no existen en el árbol.
    """
    grupo_obj = _objeto(grupo)
    sg_corteza = grupo_de(CORTEZA)
    arbol.calcular()
    todos = set(arbol.modulos)
    rehacer = todos if ids is None else set(ids) & todos
    contenedor = _contenedor_follaje(grupo_obj)
    viejos = []
    for h in _hijos(grupo_obj):
        id_ = _modulo_de(h)
        if id_ is not None and (id_ in rehacer or id_ not in todos):
            viejos.append(h)
    for h in _hijos(contenedor):
        id_ = _modulo_de(h)
        if id_ is not None and (id_ in rehacer or id_ not in todos):
            viejos.append(h)
    _borrar(viejos)
    for m in arbol._orden():
        if m.id in rehacer:
            _construir_modulo(grupo_obj, arbol, m, nivel, sg_corteza)
            _construir_follaje(contenedor, m, nivel)
    if guardar_receta:
        _atributo_texto(grupo_obj, ATRIBUTO_RECETA, arbol.a_json())
    _atributo_texto(grupo_obj, ATRIBUTO_NIVEL, nivel)
    return grupo


def crear(arbol, nivel="denso", nombre=None, posicion=None):
    """Crea un grupo nuevo con el árbol y devuelve su nombre. Llamar a preparar() antes."""
    obj = _transformada((nombre or arbol.nombre))
    if posicion:
        om.MFnTransform(obj).setTranslation(om.MVector(*posicion), om.MSpace.kTransform)
    grupo = om.MFnDagNode(obj).fullPathName()
    reconstruir(grupo, arbol, nivel)
    return grupo


def borrar(grupo):
    _borrar([_objeto(grupo)])


# --- consultas ------------------------------------------------------------------

def es_arbol(nodo):
    return existe(nodo) and leer_texto(nodo, ATRIBUTO_RECETA) is not None


def arbol_de(grupo):
    return Arbol.de_json(leer_texto(grupo, ATRIBUTO_RECETA))


def modulo_de_nodo(nodo):
    """(grupo del árbol, id del módulo) de una malla u hoja seleccionada."""
    actual = nodo
    modulo = None
    while actual:
        if modulo is None and existe(actual):
            modulo = leer_texto(actual, ATRIBUTO_MODULO) or None
        if es_arbol(actual):
            return actual, modulo
        padres = cmds.listRelatives(actual, parent=True, fullPath=True)
        actual = padres[0] if padres else None
    return None, None


def grupos_seleccionados():
    encontrados = []
    for nodo in cmds.ls(selection=True, long=True) or []:
        grupo, _ = modulo_de_nodo(nodo)
        if grupo and grupo not in encontrados:
            encontrados.append(grupo)
    return encontrados


def mallas(grupo):
    return [om.MFnDagNode(h).fullPathName() for h in _hijos(_objeto(grupo)) if _modulo_de(h)]


def triangulos(grupo):
    total = 0
    for nombre in mallas(grupo):
        total += cmds.polyEvaluate(nombre, triangle=True)
    contenedor = _contenedor_follaje(_objeto(grupo), crear=False)
    for hojas in (_hijos(contenedor) if contenedor is not None else []):
        for t in _hijos(hojas):
            camino = om.MDagPath.getAPathTo(t)
            camino.extendToShape()
            total += sum(om.MFnMesh(camino).getTriangles()[0])
    return total


def generar(grupo, nivel):
    """Reconstruye el árbol del grupo al nivel indicado (fuera del editor)."""
    if nivel not in NIVELES:
        raise ValueError("nivel desconocido: {}".format(nivel))
    preparar()
    return reconstruir(grupo, arbol_de(grupo), nivel)


def textura_cuadros(activar=True, repeticiones=8):
    """Pone (o quita) una textura de cuadros en la corteza para revisar las UVs."""
    material, _ = materiales.crear_material(CORTEZA)
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
        color = materiales.CLAY[CORTEZA][0]
        cmds.setAttr(destino, *color, type="double3")
    return activar
