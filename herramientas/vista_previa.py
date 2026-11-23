"""Vista previa de las especies sin Maya (herramienta de desarrollo).

    python3 herramientas/vista_previa.py [carpeta] [especie ...]

Dibuja cada árbol de frente, a 3/4 desde arriba y en planta, con sombreado
plano y el algoritmo del pintor. Necesita numpy y Pillow. Sirve para ajustar
siluetas y densidad rápido; el aspecto final se juzga en Arnold.
"""

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

from arboles import especies, follaje  # noqa: E402

LADO = 520
CORTEZA = np.array((120, 95, 75))
HOJA = np.array((70, 120, 50))
FONDO = (235, 235, 230)
SUELO = (200, 200, 190)


def _triangulos(malla):
    v = np.array(malla.vertices, dtype=float)
    tris, i = [], 0
    for n in malla.conteos:
        caras = malla.conexiones[i:i + n]
        for k in range(1, n - 1):
            tris.append((caras[0], caras[k], caras[k + 1]))
        i += n
    return v[np.array(tris)] if tris else np.zeros((0, 3, 3))


def geometria(arbol, nivel="medio"):
    partes = [(_triangulos(m), CORTEZA) for m in arbol.mallas(nivel)]
    for tipo, matrices in arbol.follaje().values():
        partes.append((_triangulos(follaje.combinar(tipo, nivel, matrices)), HOJA))
    tris = np.concatenate([p[0] for p in partes])
    colores = np.concatenate([np.tile(p[1], (len(p[0]), 1)) for p in partes])
    return tris, colores


def _vista(tris, colores, azimut, elevacion, escala, centro):
    a, e = math.radians(azimut), math.radians(elevacion)
    derecha = np.array((math.cos(a), 0.0, -math.sin(a)))
    hacia = np.array((math.sin(a) * math.cos(e), -math.sin(e), math.cos(a) * math.cos(e)))  # hacia la cámara... desde ella
    arriba = np.cross(derecha, hacia) * -1
    p = tris - centro
    x = p @ derecha
    y = p @ arriba
    z = p @ hacia
    normal = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    largo = np.linalg.norm(normal, axis=1)
    normal = normal / np.maximum(largo, 1e-9)[:, None]
    luz = np.array((0.4, 0.8, 0.45))
    luz /= np.linalg.norm(luz)
    sombra = 0.45 + 0.55 * np.abs(normal @ luz)
    orden = np.argsort(-z.mean(axis=1))
    img = Image.new("RGB", (LADO, LADO), FONDO)
    dib = ImageDraw.Draw(img)
    mitad = LADO / 2.0
    for k in orden:
        puntos = [(mitad + x[k, j] * escala, mitad - y[k, j] * escala) for j in range(3)]
        c = tuple(int(min(255, v)) for v in colores[k] * sombra[k])
        dib.polygon(puntos, fill=c)
    return img


def lamina(arbol, nivel="medio"):
    tris, colores = geometria(arbol, nivel)
    minimo, maximo = tris.reshape(-1, 3).min(axis=0), tris.reshape(-1, 3).max(axis=0)
    centro = (minimo + maximo) / 2.0
    tam = max(maximo - minimo) * 1.1
    escala = LADO / tam
    vistas = [_vista(tris, colores, 0, 0, escala, centro),
              _vista(tris, colores, 35, 25, escala, centro),
              _vista(tris, colores, 0, 89.9, escala, centro)]
    hoja = Image.new("RGB", (LADO * 3, LADO + 28), (255, 255, 255))
    for i, v in enumerate(vistas):
        hoja.paste(v, (i * LADO, 28))
    ImageDraw.Draw(hoja).text((8, 6), "{}  {:.0f} x {:.0f} cm  {} triángulos ({})".format(
        arbol.nombre, maximo[0] - minimo[0], maximo[1] - minimo[1], len(tris), nivel), fill=(0, 0, 0))
    return hoja


def main(carpeta=None, *nombres):
    carpeta = os.path.abspath(carpeta or os.path.join(RAIZ, "dist", "vista_previa"))
    os.makedirs(carpeta, exist_ok=True)
    for nombre in nombres or especies.ESPECIES:
        ruta = os.path.join(carpeta, nombre + ".png")
        lamina(especies.ESPECIES[nombre]()).save(ruta)
        print(ruta)


if __name__ == "__main__":
    main(*sys.argv[1:])
