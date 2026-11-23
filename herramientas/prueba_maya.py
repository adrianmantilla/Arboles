"""Prueba de las fases 0 a 4 dentro de Maya, sin interfaz (herramienta de desarrollo).

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
    construir_maya.preparar()
    inicio = time.time()
    grupo = construir_maya.crear(ejemplos.copa_redonda())
    print("  (árbol denso en {:.2f} s)".format(time.time() - inicio))
    mallas = construir_maya.mallas(grupo)
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
    mallas = construir_maya.mallas(grupo)
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
    comprobar(construir_maya.triangulos(grupo) == denso, "el follaje sobrevive a guardar y abrir")

    fase2(cmds, tmp)
    texturas(cmds, tmp)
    estilos_y_material_propio(cmds, tmp)

    cmds.unloadPlugin("arboles_plugin")
    comprobar(not cmds.pluginInfo("arboles_plugin", query=True, loaded=True), "el plugin se descarga")


def estilos_y_material_propio(cmds, tmp):
    """Estilos de textura (con las del plugin) y material propio del alumno."""
    import maya.api.OpenMaya as om
    from arboles import construir_maya as cm, especies, materiales, plantar
    from arboles import materiales_propios as mp
    from arboles import texturas as tx
    print("Estilos y material propio")
    cmds.file(new=True, force=True)
    roble = especies.ESPECIES["roble"]()
    cm.preparar(roble)
    grupo = cm.crear(roble, "bajo", "prueba_estilos")
    rutas = {}
    for estilo in ("cartoon", "estilizado", "realista"):
        materiales.cambiar_texturas("1k", estilo)
        rutas[estilo] = os.path.normpath(cmds.getAttr("arboles_roble_corteza_color.fileTextureName"))
    comprobar(os.sep + "cartoon" + os.sep in rutas["cartoon"], "estilo cartoon: las texturas apuntan a cartoon/")
    comprobar(os.sep + "estilizado" + os.sep in rutas["estilizado"], "estilo estilizado: apuntan a estilizado/")
    comprobar(not any(os.sep + e + os.sep in rutas["realista"] for e in ("cartoon", "estilizado")),
              "volver al estilo realista")
    cmds.delete(grupo)

    # material propio con imágenes del alumno
    from arboles import interfaz_maya
    biblioteca = interfaz_maya.carpeta_biblioteca()  # como el alumno: en su biblioteca
    corteza, hoja = os.path.join(tmp, "img", "corteza.png"), os.path.join(tmp, "img", "hoja.png")
    _png(corteza, (120, 80, 40))
    _png(hoja, (40, 140, 40))
    mp.registrar(biblioteca)
    try:
        juego = mp.crear(biblioteca, "Mi material", {("corteza", "color"): corteza, ("hoja", "color"): hoja})
        atlas = tx.ruta(juego, "hoja", "color", "1k")
        try:
            from PySide6 import QtGui
        except ImportError:
            from PySide2 import QtGui
        imagen = QtGui.QImage(atlas or "")
        comprobar(atlas and imagen.width() == 1024 and imagen.height() == 1024,
                  "el atlas de la hoja propia mide 1024x1024")
        arbol = especies.ESPECIES["haya"]()
        arbol.nombre, arbol.material = "Haya de Ana", juego
        copias = [plantar.plantar(arbol, (i * 500.0, 0.0, 0.0), "bajo") for i in range(2)]
        maestro = cmds.getAttr(copias[0] + "." + plantar.ATRIBUTO_PLANTADO)
        archivos = [cmds.getAttr(n + ".fileTextureName") for n in cmds.ls("arboles_{}_*".format(juego), type="file")]
        comprobar(archivos and all(biblioteca in os.path.normpath(a) for a in archivos),
                  "el árbol con material propio usa sus imágenes ({} file)".format(len(archivos)))
        _png(hoja, (200, 180, 40))
        mp.crear(biblioteca, "Mi material", {("corteza", "color"): corteza, ("hoja", "color"): hoja})
        rehechos = materiales.rehacer_material_texturas(juego)
        sin_material = []
        for forma in cmds.listRelatives(maestro, allDescendents=True, type="mesh", fullPath=True) or []:
            for camino in om.MDagPath.getAllPathsTo(cm._objeto(forma)):
                if not om.MFnMesh(camino).getConnectedShaders(camino.instanceNumber())[0]:
                    sin_material.append(camino.fullPathName())
        comprobar(rehechos and not sin_material,
                  "rehacer el material propio lo mantiene en las copias plantadas ({} sin él)".format(len(sin_material)))
    finally:
        mp.registrar(biblioteca)
    cmds.file(new=True, force=True)


def _png(ruta, color):
    """PNG de 4x4 de un color, sin bibliotecas externas."""
    import struct
    import zlib

    def trozo(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos) & 0xffffffff)
    filas = b"".join(b"\x00" + bytes(color) * 4 for _ in range(4))
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + trozo(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0))
                + trozo(b"IDAT", zlib.compress(filas)) + trozo(b"IEND", b""))


def texturas(cmds, tmp):
    """Material por especie: juego de prueba en una carpeta temporal."""
    print("Texturas por especie")
    from arboles import construir_maya as cm, especies, materiales
    from arboles import texturas as tx
    cmds.file(new=True, force=True)  # sin los materiales reales que dejó la fase 2
    carpeta = os.path.join(tmp, "texturas")
    original = tx.carpeta_texturas
    tx.carpeta_texturas = lambda: carpeta
    try:
        for res in ("512", "1k"):
            for parte, canales in (("corteza", ("color", "normal", "rugosidad")),
                                   ("hoja", ("color", "normal", "rugosidad", "translucidez"))):
                for canal in canales:
                    _png(os.path.join(carpeta, "roble", res, "{}_{}.png".format(parte, canal)), (90, 120, 60))
        comprobar(tx.existe("roble") and not tx.existe("haya"), "juego de texturas «roble» instalado (prueba)")
        roble = especies.ESPECIES["roble"]()
        cm.preparar(roble)
        comprobar(cmds.objExists("arboles_roble_corteza") and cmds.objExists("arboles_roble_hoja"),
                  "preparar crea los materiales del roble")
        grupo = cm.crear(roble, "bajo", "prueba_roble")
        tronco = cmds.listRelatives(cm.mallas(grupo)[0], shapes=True, fullPath=True)[0]
        comprobar(cm.grupo_de("arboles_roble_corteza") in (cmds.listConnections(tronco, type="shadingEngine") or []),
                  "el tronco del roble usa su corteza con texturas")
        ruta = cmds.getAttr("arboles_roble_corteza_color.fileTextureName")
        comprobar(os.path.normpath(ruta).endswith(os.path.join("1k", "corteza_color.png")), "texturas a 1K por defecto")
        comprobar(cmds.isConnected("arboles_roble_corteza_relieve.outNormal", "arboles_roble_corteza.normalCamera"),
                  "mapa de normales conectado")
        comprobar(cmds.isConnected("arboles_roble_hoja_translucidez.outColor", "arboles_roble_hoja.subsurfaceColor"),
                  "translucidez de la hoja conectada")
        cambiadas = materiales.cambiar_resolucion("512")
        ruta = cmds.getAttr("arboles_roble_corteza_color.fileTextureName")
        comprobar(cambiadas == 7 and os.sep + "512" + os.sep in os.path.normpath(ruta),
                  "cambiar la resolución a 512 ({} imágenes)".format(cambiadas))
        haya = especies.ESPECIES["haya"]()
        cm.preparar(haya)
        otro = cm.crear(haya, "bajo", "prueba_haya")
        tronco = cmds.listRelatives(cm.mallas(otro)[0], shapes=True, fullPath=True)[0]
        comprobar(cm.grupo_de(cm.CORTEZA) in (cmds.listConnections(tronco, type="shadingEngine") or []),
                  "una especie sin texturas instaladas se queda en clay")
        cmds.delete(grupo, otro)
        # Un maestro de una escena anterior en clay se rehace con texturas al volver a plantar.
        from arboles import plantar
        viejo = especies.ESPECIES["roble"]()
        viejo.material = "clay"
        ruta_maestro = plantar.asegurar_maestro(viejo, "bajo")
        nuevo = especies.ESPECIES["roble"]()
        plantar.plantar(nuevo, (0.0, 0.0, 0.0), "bajo")
        comprobar(plantar._materiales_al_dia(ruta_maestro, nuevo),
                  "un maestro viejo en clay se rehace con las texturas de su especie")
        cmds.file(new=True, force=True)
    finally:
        tx.carpeta_texturas = original


def fase2(cmds, tmp):
    import time
    import maya.api.OpenMaya as om
    from arboles import acciones, ejemplos
    from arboles import construir_maya as cm
    from arboles import editor as ed
    from arboles import modulos as mod
    from arboles.biblioteca import Biblioteca

    print("Fase 2")
    cmds.file(new=True, force=True)
    cmds.undoInfo(state=True, infinity=True)
    comprobar(acciones.hay_comando(), "el comando arbolesAccion está registrado")
    e = ed.Editor().abrir("copa_redonda")
    avisos = []
    e.oyentes.append(lambda: avisos.append(1))
    comprobar(cm.es_arbol(ed.GRUPO), "el editor crea su grupo con receta")
    tri0 = cm.triangulos(e.grupo)
    comprobar(tri0 == e.arbol.triangulos("denso"), "triángulos con follaje iguales a los calculados ({})".format(tri0))

    # follaje: una malla por rama
    contenedor = cm._contenedor_follaje(cm._objeto(e.grupo), crear=False)
    grupos_hojas = cm._hijos(contenedor) if contenedor is not None else []
    comprobar(len(grupos_hojas) == len(e.arbol.follaje()), "una malla de hojas por rama con follaje ({})".format(len(grupos_hojas)))
    hojas = cm._nombre(grupos_hojas[0])
    forma_hojas = cmds.listRelatives(hojas, shapes=True, fullPath=True)[0]
    comprobar(cm.grupo_de(cm.HOJA) in (cmds.listConnections(forma_hojas, type="shadingEngine") or []),
              "las hojas llevan el material clay de hoja")

    ramas = [i for i, m in e.arbol.modulos.items() if m.tipo == mod.RAMA]
    rama, otra = ramas[0], ramas[1]
    largo0 = e.arbol.modulos[rama].valores["longitud"]
    largo_otra = e.arbol.modulos[otra].valores["longitud"]

    # deslizador: vista previa y un solo paso de deshacer
    inicio = time.time()
    e.empezar_cambio([rama])
    for x in (largo0 + 10, largo0 + 30, largo0 + 50):
        e.cambiar_valor([rama], "longitud", x)
    print("  (3 pasos de arrastre en {:.2f} s)".format(time.time() - inicio))
    inicio = time.time()
    e.terminar_cambio()
    print("  (soltar y reconstruir denso en {:.2f} s)".format(time.time() - inicio))
    comprobar(cm.arbol_de(e.grupo).modulos[rama].valores["longitud"] == largo0 + 50, "el cambio queda en la receta")
    comprobar(cm.triangulos(e.grupo) == e.arbol.triangulos("denso"), "tras soltar, malla densa al día")
    cmds.undo()
    comprobar(e.arbol.modulos[rama].valores["longitud"] == largo0, "Ctrl+Z deshace el arrastre entero")
    comprobar(cm.arbol_de(e.grupo).modulos[rama].valores["longitud"] == largo0, "deshacer restaura la receta")
    comprobar(cm.triangulos(e.grupo) == tri0, "deshacer restaura las mallas")
    cmds.redo()
    comprobar(e.arbol.modulos[rama].valores["longitud"] == largo0 + 50, "rehacer vuelve a aplicarlo")
    comprobar(avisos, "la ventana se entera de los cambios")
    cmds.undo()

    # edición en grupo, relativa
    e.empezar_cambio([rama, otra])
    e.cambiar_valor([rama, otra], "longitud", largo0 + 40, rama)
    e.terminar_cambio()
    comprobar(abs(e.arbol.modulos[otra].valores["longitud"] - (largo_otra + 40)) < 1e-6,
              "editar varias ramas suma el mismo cambio a cada una")
    cmds.undo()

    # añadir, repetir, quitar, plantillas
    n = len(e.arbol.modulos)
    nueva = e.anadir_rama(rama)
    comprobar(nueva in e.arbol.modulos and len(cm.mallas(e.grupo)) == n + 1, "añadir rama")
    cmds.undo()
    comprobar(len(cm.mallas(e.grupo)) == n and nueva not in e.arbol.modulos, "deshacer añadir rama")
    copias = e.repetir(rama, 3)
    comprobar(len(copias) == 3 and len(e.arbol.modulos) == n + 3 * (1 + len(e.arbol.descendientes(rama))),
              "repetir alrededor con descendientes")
    cmds.undo()
    e.quitar([e.arbol.tronco.id])
    comprobar(e.arbol.tronco is not None, "el tronco no se puede quitar")
    e.quitar([rama])
    comprobar(rama not in e.arbol.modulos, "quitar rama")
    cmds.undo()
    comprobar(rama in e.arbol.modulos and len(cm.mallas(e.grupo)) == n, "deshacer quitar rama")
    e.pegar({"longitud": 77.0, "posicion": 0.01}, [otra])
    comprobar(e.arbol.modulos[otra].valores["longitud"] == 77.0, "pegar ajustes")
    cmds.undo()
    e.nueva("sauce_lloron")
    comprobar(len(e.arbol.modulos) == len(ejemplos.PLANTILLAS["sauce_lloron"]().modulos), "empezar desde plantilla")
    cmds.undo()
    comprobar(len(e.arbol.modulos) == n, "deshacer plantilla")

    # tiradores de la curva
    e.mostrar_tiradores(rama)
    tiradores = cmds.listRelatives(ed.TIRADORES, children=True) or []
    comprobar(len(tiradores) == 3, "3 tiradores en la rama")
    punta = e.arbol.modulos[rama].guia.punto(1.0)
    cmds.move(0, 40, 0, ed.TIRADORES + "|" + tiradores[2], relative=True)
    e._tirador_movido()  # en Maya con interfaz lo llama el scriptJob
    comprobar(abs(e.arbol.modulos[rama].guia.punto(1.0)[1] - punta[1] - 40) < 0.5, "mover un tirador curva la rama")
    comprobar(cm.arbol_de(e.grupo).modulos[rama].curva, "la curva a mano queda en la receta")
    e.enderezar([rama])
    comprobar(not e.arbol.modulos[rama].curva, "enderezar")
    e.quitar_tiradores()
    comprobar(not cmds.objExists(ed.TIRADORES), "quitar tiradores")

    # clic en el visor (rayo)
    tronco = e.arbol.tronco.id
    id_, punto = e.modulo_bajo_rayo((0.0, 120.0, 5000.0), (0.0, 0.0, -1.0))
    comprobar(id_ == tronco, "un rayo hacia la base encuentra el tronco ({})".format(id_))
    if id_:
        sitio = e.rama_en_punto(id_, punto)
        comprobar(abs(sitio["giro"] - 0) >= 0 and 0 <= sitio["posicion"] <= 0.4, "posición de la rama en el clic ({:.2f})".format(sitio["posicion"]))
        nueva = e.anadir_rama(id_, **sitio)
        e.arbol.calcular()
        base = e.arbol.modulos[nueva].guia.punto(0.0)
        comprobar(v_dist(base, punto) < e.arbol.modulos[tronco].valores["grosor"] * 1.5,
                  "la rama nace donde se hizo clic ({:.1f} cm)".format(v_dist(base, punto)))
        cmds.undo()

    # selección
    e.seleccionar([rama, otra])
    comprobar(sorted(e.ids_seleccionados_en_visor()) == sorted([rama, otra]), "selección entre lista y visor")

    # figura humana
    e.figura_humana(True)
    comprobar(cmds.objExists(ed.FIGURA), "figura humana")
    caja = cmds.exactWorldBoundingBox(ed.FIGURA)
    comprobar(abs(caja[4] - caja[1] - 174) < 2, "la figura mide 1,75 m ({:.0f} cm)".format(caja[4] - caja[1]))
    e.figura_humana(False)
    comprobar(not cmds.getAttr(ed.FIGURA + ".visibility"), "ocultar figura")

    # Generar
    for nivel in mod.NIVELES_GENERAR:
        inicio = time.time()
        g = e.generar(nivel)
        segundos = time.time() - inicio
        comprobar(g and cm.es_arbol(g) and cm.triangulos(g) == e.arbol.triangulos(nivel),
                  "Generar {}: {} triángulos en {:.2f} s".format(nivel, cm.triangulos(g) if g else "-", segundos))
    cmds.undo()
    comprobar(not cm.existe(g), "deshacer Generar")
    cmds.redo()
    comprobar(cm.existe(g), "rehacer Generar")
    cmds.delete(g)
    comprobar(cm.triangulos(e.grupo) == e.arbol.triangulos("denso"), "borrar la copia no toca el árbol del editor")

    # biblioteca
    bib = Biblioteca(os.path.join(tmp, "Documents", "Arboles"))
    e.renombrar("Arce del patio")
    comprobar(e.arbol.nombre == "Arce del patio", "renombrar")
    bib.guardar(e.arbol)
    bib.guardar_rama("rama buena", e.arbol.subarbol(rama))
    e.nueva("vacio")
    e.cargar(bib.cargar("Arce del patio"))
    comprobar(e.arbol.nombre == "Arce del patio" and len(e.arbol.modulos) == n, "abrir de la biblioteca")
    nueva = e.injertar(bib.cargar_rama("rama_buena"), e.arbol.tronco.id)
    comprobar(nueva in e.arbol.modulos, "insertar rama favorita")

    # cerrar y volver a abrir el editor recupera el árbol
    e.cerrar()
    otra_vez = ed.Editor().abrir("vacio")
    comprobar(len(otra_vez.arbol.modulos) == len(e.arbol.modulos), "reabrir el editor recupera el árbol")

    fase3(cmds, tmp, bib)
    ventana(cmds, tmp, otra_vez)


def fase3(cmds, tmp, bib):
    import maya.api.OpenMaya as om
    from arboles import construir_maya as cm
    from arboles import ejemplos, plantar

    print("Fase 3")
    cmds.file(new=True, force=True)
    arbol = ejemplos.crear("roble", "frondosa")
    arbol.nombre = "Roble del patio"
    bib.guardar(arbol)
    arbol = bib.cargar("Roble_del_patio")
    suelo = cmds.polyPlane(width=4000, height=4000, name="suelo")[0]
    cmds.move(0, 50, 0, suelo)
    punto = plantar.punto_en_suelo((300.0, 1000.0, 200.0), (0.0, -1.0, 0.0))
    comprobar(punto and abs(punto[1] - 50) < 1e-3, "el clic encuentra el suelo ({})".format(punto))
    copias = [plantar.plantar(arbol, (i * 600.0, 50.0, 0.0)) for i in range(3)]
    maestro = plantar.ruta_maestro(arbol.nombre, "medio")
    comprobar(cm.es_arbol(maestro), "se crea el maestro oculto")
    comprobar(len(plantar.plantados()) == 3, "3 copias plantadas")
    caminos = om.MDagPath.getAllPathsTo(cm._objeto(maestro))
    comprobar(len(caminos) == 4, "las copias son instancias del maestro ({} caminos)".format(len(caminos)))
    giros = {round(cmds.getAttr(c + ".rotateY"), 3) for c in copias}
    comprobar(len(giros) == 3, "cada copia con su giro aleatorio")
    punto = plantar.punto_en_suelo((0.0, 3000.0, 0.0), (0.0, -1.0, 0.0))
    comprobar(punto and abs(punto[1] - 50) < 1e-3, "el clic atraviesa los árboles y planta en el suelo")
    n, tri = plantar.informe()
    comprobar(n == 3 and tri == 3 * cm.triangulos(maestro), "recuento del jardín ({} triángulos)".format(tri))
    cmds.undo()
    comprobar(len(plantar.plantados()) == 2, "deshacer la última copia plantada")
    cmds.redo()
    comprobar(len(plantar.plantados()) == 3, "rehacerla")

    # cambiar el maestro cambia todas las copias
    antes = cm.triangulos(maestro)
    cambiado = arbol.copiar()
    for m in cambiado.modulos.values():
        if m.tipo == "rama":
            m.fijar("densidad", 0.1)
    comprobar(plantar.actualizar_maestros(cambiado) == 1, "actualizar el maestro")
    despues = cm.triangulos(maestro)
    comprobar(despues < antes and despues == cambiado.triangulos("medio"),
              "las copias cambian con el maestro ({} → {})".format(antes, despues))
    comprobar(len(om.MDagPath.getAllPathsTo(cm._objeto(maestro))) == 4, "siguen siendo instancias tras actualizar")
    sin_material = []
    for forma in cmds.listRelatives(maestro, allDescendents=True, type="mesh", fullPath=True) or []:
        for camino in om.MDagPath.getAllPathsTo(cm._objeto(forma)):
            if not om.MFnMesh(camino).getConnectedShaders(camino.instanceNumber())[0]:
                sin_material.append(camino.fullPathName())
    comprobar(not sin_material, "todas las copias tienen material tras actualizar ({} sin él)".format(len(sin_material)))
    cmds.undo()
    comprobar(cm.triangulos(maestro) == antes, "deshacer la actualización")

    # desligar
    libres = plantar.desligar([copias[0]])
    comprobar(len(libres) == 1 and len(plantar.plantados()) == 2, "desligar una copia")
    comprobar(cm.triangulos(maestro) == antes and len(om.MDagPath.getAllPathsTo(cm._objeto(maestro))) == 3,
              "desligar no toca el maestro ni las otras copias")
    hijos = cmds.listRelatives(libres[0], children=True, fullPath=True) or []
    comprobar(hijos and len(om.MDagPath.getAllPathsTo(cm._objeto(hijos[0]))) == 1, "la copia desligada es independiente")
    cmds.undo()
    comprobar(len(plantar.plantados()) == 3, "deshacer desligar")

    # borrar una copia no toca el maestro
    cmds.delete(copias[2])
    comprobar(cm.es_arbol(maestro) and len(plantar.plantados()) == 2, "borrar una copia deja el maestro")

    # variaciones por copia: formas distintas (maestros por variante), tamaño e inclinación
    import random
    random.seed(5)
    palmera = ejemplos.crear("palmera")
    variadas = [plantar.plantar(palmera, (i * 300.0, 50.0, 3000.0), "bajo", variantes=4, tamano=0.2,
                                inclinacion=8.0) for i in range(16)]
    formas = sorted({cmds.getAttr(c + "." + plantar.ATRIBUTO_PLANTADO) for c in variadas})
    comprobar(len(formas) == 4, "4 formas repartidas entre 16 copias ({})".format(len(formas)))
    comprobar(sorted(plantar.variante_de(f) for f in formas) == [0, 1, 2, 3], "un maestro por variante")
    comprobar(len({cm.triangulos(f) for f in formas}) > 1 or len({str(cmds.exactWorldBoundingBox(f)) for f in formas}) == 4,
              "las variantes tienen forma distinta")
    comprobar(all(cm.arbol_de(f).a_dict() == palmera.a_dict() for f in formas),
              "las variantes guardan la receta del original (Editar maestro abre el original)")
    escalas = [cmds.getAttr(c + ".scaleX") for c in variadas]
    inclinaciones = [max(abs(cmds.getAttr(c + ".rotateX")), abs(cmds.getAttr(c + ".rotateZ"))) for c in variadas]
    comprobar(all(0.8 - 1e-6 <= e <= 1.2 + 1e-6 for e in escalas) and len({round(e, 4) for e in escalas}) > 8,
              "tamaño al azar dentro de ±20 %")
    comprobar(all(i <= 8.0 + 1e-6 for i in inclinaciones) and max(inclinaciones) > 1.0, "inclinación al azar hasta 8°")
    otra = palmera.copiar()
    for m in otra.modulos.values():
        if m.tipo == "rama":
            m.fijar("densidad", 0.5)
    comprobar(plantar.actualizar_maestros(otra) == 4, "actualizar el original rehace sus 4 variantes")
    comprobar(all(cm.arbol_de(f).a_dict() == otra.a_dict() for f in formas), "las variantes siguen al original")
    cmds.delete(variadas)

    # «Usar como hoja»: una malla del alumno como hoja de un árbol
    from arboles import follaje, hoja_maya
    hoja = cmds.polyPlane(width=8, height=20, subdivisionsX=2, subdivisionsY=3, axis=(0, 0, 1), name="hoja_alumno")[0]
    cmds.move(0, 10, 0, hoja)
    cmds.select(hoja)
    forma = hoja_maya.malla_seleccionada()
    datos = hoja_maya.leer_hoja(forma)
    tipo = bib.guardar_hoja("Hoja alumno", datos)
    ys = [p[1] for p in datos["vertices"]]
    comprobar(tipo == "propia:Hoja_alumno" and len(datos["vertices"]) == 12 and abs(min(ys)) < 1e-6
              and abs(max(ys) - 1.0) < 1e-6, "leer la malla del alumno como hoja (tallo abajo, largo 1)")
    comprobar(len(datos["uvs"]) == 12, "la hoja conserva sus UV")
    haya = ejemplos.crear("haya")
    for m in haya.modulos.values():
        if m.valores.get("follaje", "ninguno") != "ninguno":
            m.fijar("follaje", tipo)
    cm.preparar(haya)
    grupo = cm.crear(haya, "medio", "prueba_hoja_propia")
    comprobar(cm.triangulos(grupo) == haya.triangulos("medio") and haya.triangulos("medio") > haya.triangulos(
        "medio", con_follaje=False), "un árbol con la hoja propia se construye ({} triángulos)".format(cm.triangulos(grupo)))
    comprobar("Hoja_alumno" in cm.arbol_de(grupo).a_dict().get("hojas_propias", {}),
              "la receta del árbol lleva su hoja propia")
    follaje.HOJAS_PROPIAS.clear()
    comprobar(bib.cargar_hojas() == [tipo], "la biblioteca guarda la hoja propia")
    cmds.delete(grupo, hoja)

    # horquilla: el tronco se divide en 3 brazos y las ramas de encima nacen en ellos
    from arboles import modulos as mod
    castano = ejemplos.crear("castano")
    castano.tronco.fijar("horquilla", 0.45)
    castano.tronco.fijar("brazos", 3)
    cm.preparar(castano)
    grupo = cm.crear(castano, "medio", "prueba_horquilla")
    tronco_malla = cm.mallas(grupo)[0]
    comprobar(cm.triangulos(grupo) == castano.triangulos("medio") and cmds.polyEvaluate(tronco_malla, face=True) > 0,
              "un árbol con horquilla de 3 brazos se construye ({} triángulos)".format(cm.triangulos(grupo)))
    castano.calcular()
    guia = castano.tronco.guia
    lejos = []
    for m in castano.hijos(castano.tronco.id):
        if m.tipo != mod.RAMA or m.valores["posicion"] <= 0.45:
            continue
        origen = m.guia.punto(0.0)
        cerca = min(v_dist(origen, b.punto(k / 40.0)) - b.radio_medio(k / 40.0)
                    for b in guia.brazos for k in range(41))
        if cerca > 15.0:
            lejos.append(round(cerca, 1))
    comprobar(len(guia.brazos) == 3 and not lejos, "las ramas altas nacen en un brazo ({} lejos: {})".format(len(lejos), lejos))
    cmds.delete(grupo)

    # árboles de ejemplo en una biblioteca vacía
    from arboles.biblioteca import Biblioteca
    bib_ejemplos = Biblioteca(os.path.join(tmp, "biblioteca_ejemplos"))
    nuevos = plantar.anadir_ejemplos(bib_ejemplos)
    comprobar(len(nuevos) == len(ejemplos.PLANTILLAS) - 1 and len(bib_ejemplos.arboles()) == len(nuevos),
              "botón Ejemplos llena la biblioteca ({} árboles)".format(len(nuevos)))
    comprobar(plantar.anadir_ejemplos(bib_ejemplos) == [] and not cmds.ls("arboles_ejemplo_temporal*"),
              "Ejemplos no repite ni deja restos en la escena")

    archivo = os.path.join(tmp, "jardin.ma")
    cmds.file(rename=archivo)
    cmds.file(save=True, type="mayaAscii", force=True)
    cmds.file(archivo, open=True, force=True)
    comprobar(len(plantar.plantados()) == 2 and len(om.MDagPath.getAllPathsTo(cm._objeto(maestro))) == 3,
              "el jardín sobrevive a guardar y abrir")


def v_dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def ventana(cmds, tmp, editor):
    """Crea la ventana Qt fuera de pantalla y guarda una captura (si hay Qt)."""
    try:
        try:
            from PySide6 import QtWidgets
        except ImportError:
            from PySide2 import QtWidgets
        app = QtWidgets.QApplication.instance()
        if not isinstance(app, QtWidgets.QApplication):
            # mayapy solo trae QCoreApplication: la ventana se prueba en Maya con interfaz
            print("  (sin interfaz: la ventana se prueba con herramientas/captura_editor.py)")
            return
        from arboles import editor_ui
        w = editor_ui.VentanaEditor(padre=QtWidgets.QWidget())
        w.show()
        app.processEvents()
        fila = w._filas.get("altura")
        comprobar(fila is not None, "la ventana muestra los deslizadores del tronco")
        w._seleccionar_ids([i for i in w.editor.arbol.modulos if i != w.editor.arbol.tronco.id][:2])
        app.processEvents()
        comprobar("follaje" in w._filas, "con ramas seleccionadas aparece el bloque Follaje")
        destino = os.environ.get("ARBOLES_CAPTURA") or os.path.join(tmp, "editor.png")
        w.grab().save(destino)
        print("  captura de la ventana: " + destino)
        w.close()
    except Exception:
        traceback.print_exc()
        comprobar(False, "la ventana del editor se crea")


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
