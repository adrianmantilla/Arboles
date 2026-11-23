"""Juegos de texturas por especie (sin Maya).

Cada juego vive en ``<plugin>/texturas/<juego>/<resolución>/`` con una imagen
por canal::

    corteza_color   corteza_normal   corteza_rugosidad
    hoja_color      hoja_normal      hoja_rugosidad   hoja_translucidez

Formatos: .png, .jpg, .tif o .exr. Si falta la resolución pedida se usa la más
cercana que haya. Un árbol con material «clay», o con un juego que no existe,
se queda en clay.

La corteza es repetible: su UV da una vuelta entera de textura por cada
«escala_textura» cm. La hoja ocupa toda la imagen: u a lo ancho (0,5 es el
nervio) y v a lo largo, del tallo (0) a la punta (1).
"""

import os

CLAY = "clay"
RESOLUCIONES = ("512", "1k", "2k", "4k")
RESOLUCION_POR_DEFECTO = "1k"
PARTES = ("corteza", "hoja")
CANALES = ("color", "normal", "rugosidad", "translucidez")
_EXTENSIONES = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr")


def carpeta_texturas():
    """<raíz del plugin>/texturas (junto a scripts/ y plug-ins/)."""
    aqui = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(aqui, "..", "..", "texturas"))


def juegos(carpeta=None):
    carpeta = carpeta or carpeta_texturas()
    if not os.path.isdir(carpeta):
        return []
    return sorted(d for d in os.listdir(carpeta)
                  if not d.startswith(".") and os.path.isdir(os.path.join(carpeta, d)))


def existe(juego, carpeta=None):
    return bool(juego) and juego != CLAY and juego in juegos(carpeta)


def _orden_resoluciones(resolucion):
    i = RESOLUCIONES.index(resolucion) if resolucion in RESOLUCIONES else RESOLUCIONES.index(RESOLUCION_POR_DEFECTO)
    return sorted(RESOLUCIONES, key=lambda r: (abs(RESOLUCIONES.index(r) - i), -RESOLUCIONES.index(r)))


def ruta(juego, parte, canal, resolucion=RESOLUCION_POR_DEFECTO, carpeta=None):
    """Imagen de ``parte``/``canal`` del juego, o None si no hay."""
    carpeta = carpeta or carpeta_texturas()
    for res in _orden_resoluciones(resolucion):
        base = os.path.join(carpeta, juego, res, "{}_{}".format(parte, canal))
        for ext in _EXTENSIONES:
            if os.path.isfile(base + ext):
                return base + ext
    return None


def canales(juego, parte, resolucion=RESOLUCION_POR_DEFECTO, carpeta=None):
    """{canal: ruta} con los canales que existen."""
    resultado = {}
    for canal in CANALES:
        r = ruta(juego, parte, canal, resolucion, carpeta)
        if r:
            resultado[canal] = r
    return resultado
