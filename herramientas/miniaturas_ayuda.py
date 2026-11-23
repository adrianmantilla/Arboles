"""Miniaturas de la ayuda de cada deslizador del editor (herramienta de desarrollo).

    python3 herramientas/miniaturas_ayuda.py [carpeta]

Para cada parámetro numérico de tronco y rama dibuja el mismo árbol con un valor bajo
y uno alto, uno al lado del otro, y lo guarda en ``iconos/ayuda/<tipo>_<parámetro>.png``.
El editor la enseña bajo la frase de ayuda al pasar el ratón. Necesita numpy y Pillow
(usa el dibujo de herramientas/vista_previa.py).
"""

import os
import sys

import numpy as np
from PIL import Image, ImageDraw

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arboles import modulos as mod  # noqa: E402
from arboles.arbol import Arbol  # noqa: E402
import vista_previa as vp  # noqa: E402

LADO = 150          # cada mitad
FONDO = (246, 246, 242)

# Valores (bajo, alto) donde el rango completo no se ve bien; el resto usa el 15 % y el 85 % del rango
VALORES = {
    ("tronco", "altura"): (300.0, 700.0),
    ("tronco", "grosor"): (12.0, 40.0),
    ("tronco", "inclinacion"): (0.0, 30.0),
    ("tronco", "curvatura"): (0.0, 0.8),
    ("tronco", "direccion"): (90.0, 270.0),
    ("tronco", "torsion"): (0.0, 300.0),
    ("tronco", "nudos"): (0, 8),
    ("tronco", "raices"): (0.0, 1.0),
    ("tronco", "irregularidad"): (0.0, 1.0),
    ("rama", "irregularidad"): (0.0, 1.0),
    ("tronco", "horquilla"): (0.0, 0.45),
    ("tronco", "abertura"): (12.0, 55.0),
    ("rama", "longitud"): (120.0, 320.0),
    ("rama", "angulo"): (25.0, 85.0),
    ("rama", "curvatura"): (-0.5, 0.7),
    ("rama", "posicion"): (0.3, 0.9),
    ("rama", "giro"): (90.0, 270.0),
    ("rama", "torsion"): (0.0, 300.0),
    ("rama", "nudos"): (0, 6),
}
# Vista: (azimut, elevación); por defecto de frente
VISTAS = {("rama", "giro"): (0, 70), ("tronco", "brazos"): (0, 60),
          ("tronco", "raices"): (20, 25)}
# Detalles que solo se ven de cerca: la base del tronco o la rama sola
DE_CERCA = {("tronco", "raices"), ("tronco", "irregularidad"), ("tronco", "nudos"),
            ("rama", "irregularidad"), ("rama", "nudos"), ("rama", "grosor"), ("rama", "estrechamiento")}
# Sin miniatura: sin textura no se ve (la torsión gira la corteza sobre sí misma)
SIN_MINIATURA = {("tronco", "torsion"), ("rama", "torsion"), ("rama", "irregularidad")}


def valores(tipo, nombre):
    if (tipo, nombre) in VALORES:
        return VALORES[(tipo, nombre)]
    defecto, minimo, maximo, _ = mod.PARAMETROS[tipo][nombre]
    bajo, alto = minimo + 0.15 * (maximo - minimo), minimo + 0.85 * (maximo - minimo)
    if isinstance(defecto, int):
        return int(round(minimo)), int(round(maximo))
    return bajo, alto


def arbol_tronco(nombre, valor):
    """Tronco solo (o con unas ramas si el parámetro afecta a dónde nacen)."""
    a = Arbol("ayuda_" + nombre)
    base = dict(altura=500, grosor=24, estrechamiento=0.35, curvatura=0.1, raices=0.4,
                irregularidad=0.25, nudos=2)
    if nombre in ("brazos", "abertura"):
        base["horquilla"] = 0.45
    if nombre == "direccion":
        base["inclinacion"] = 25
    base[nombre] = valor
    t = a.anadir_tronco(**base)
    if nombre in ("horquilla", "brazos", "abertura", "altura", "inclinacion", "curvatura", "direccion"):
        for i, giro in enumerate((30, 150, 270, 90, 210, 330)):
            a.anadir_rama(t, posicion=0.55 + 0.07 * i, giro=giro, angulo=50, longitud=170, caida=0.25,
                          grosor=0.4, follaje="ninguno")
    return a


def arbol_rama(nombre, valor):
    """Tronco con una rama de perfil (y hojas si el parámetro es de follaje)."""
    a = Arbol("ayuda")
    t = a.anadir_tronco(altura=420, grosor=16, estrechamiento=0.4, curvatura=0.0, raices=0.2,
                        irregularidad=0.1, nudos=0)
    con_hojas = nombre in mod.PARAMETROS_FOLLAJE
    gruesa = nombre in ("irregularidad", "nudos")
    rama = dict(posicion=0.55, giro=90, angulo=55, longitud=130 if gruesa else 250, caida=0.3, curvatura=0.1,
                grosor=0.9 if gruesa else 0.5,
                follaje="hoja_ancha" if con_hojas else "ninguno", densidad=0.8, zona=0.6)
    rama[nombre] = valor
    a.anadir_rama(t, **rama)
    return a


def _imagen(arbol, centro, escala, vista):
    tris, colores = vp.geometria(arbol, "alto")
    im = vp._vista(tris, colores, vista[0], vista[1], escala, centro)
    return im.resize((LADO, LADO), Image.LANCZOS)


def _puntos_encuadre(arbol, tipo, cerca):
    """Puntos que deben caber en la imagen: todo el árbol, o de cerca la base del tronco o la rama."""
    if not cerca:
        return vp.geometria(arbol, "alto")[0].reshape(-1, 3)
    mallas = arbol.mallas("alto")
    if tipo == "tronco":
        p = np.array(mallas[0].vertices, dtype=float)
        alto = 0.7 if "nudos" in arbol.nombre else 0.35
        return p[p[:, 1] < p[:, 1].min() + alto * (p[:, 1].max() - p[:, 1].min())]
    return np.array(mallas[1].vertices, dtype=float)


def _texto_valor(x):
    return "{:g}".format(round(x, 2))


def miniatura(tipo, nombre):
    crear = arbol_tronco if tipo == "tronco" else arbol_rama
    bajo, alto = valores(tipo, nombre)
    arboles = [crear(nombre, bajo), crear(nombre, alto)]
    puntos = np.concatenate([_puntos_encuadre(a, tipo, (tipo, nombre) in DE_CERCA) for a in arboles])
    minimo, maximo = puntos.min(axis=0), puntos.max(axis=0)
    centro = (minimo + maximo) / 2.0
    escala = vp.LADO / (max(maximo - minimo) * 1.08)
    vista = VISTAS.get((tipo, nombre), (0, 0))
    hoja = Image.new("RGB", (LADO * 2 + 24, LADO + 18), FONDO)
    dib = ImageDraw.Draw(hoja)
    for i, a in enumerate(arboles):
        im = _imagen(a, centro, escala, vista)
        hoja.paste(im, (i * (LADO + 24), 0))
    # Flecha de «menos» a «más»
    y = LADO // 2
    dib.line((LADO + 4, y, LADO + 20, y), fill=(90, 90, 90), width=2)
    dib.polygon([(LADO + 20, y - 5), (LADO + 20, y + 5), (LADO + 24, y)], fill=(90, 90, 90))
    for i, texto in enumerate((_texto_valor(bajo), _texto_valor(alto))):
        dib.text((i * (LADO + 24) + 4, LADO + 3), texto, fill=(60, 60, 60))
    return hoja


def parametros():
    for tipo in mod.TIPOS:
        for nombre, (defecto, _, _, _) in mod.PARAMETROS[tipo].items():
            if nombre in mod.OPCIONES or (tipo, nombre) in SIN_MINIATURA:
                continue
            yield tipo, nombre


def main(carpeta=None):
    vp.FONDO = FONDO
    carpeta = os.path.abspath(carpeta or os.path.join(RAIZ, "iconos", "ayuda"))
    os.makedirs(carpeta, exist_ok=True)
    for tipo, nombre in parametros():
        ruta = os.path.join(carpeta, "{}_{}.png".format(tipo, nombre))
        miniatura(tipo, nombre).save(ruta, optimize=True)
        print(ruta)


if __name__ == "__main__":
    main(*sys.argv[1:])
