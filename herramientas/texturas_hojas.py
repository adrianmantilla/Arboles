"""Genera por código las texturas de hoja (o aguja) de cada especie.

    python3 herramientas/texturas_hojas.py [carpeta de salida] [especie ...]

Necesita numpy y Pillow. Por defecto escribe en ``texturas/`` del plugin::

    <especie>/<512|1k>/hoja_color.jpg, hoja_normal.jpg, hoja_rugosidad.jpg, hoja_translucidez.jpg

La imagen lleva cuatro variantes de la hoja en 2x2, con algo de color distinto
(cada hoja del grupo usa una al azar). En cada cuarto, u va a lo ancho (el
nervio en el centro) y v a lo largo, del tallo (abajo) a la punta (arriba). Las hojas son pequeñas en
pantalla, así que no hace falta más de 1K: si se pide 2K o 4K, el plugin usa 1K.
Todo sale de una semilla fija: el resultado es siempre el mismo.
"""

import os
import sys

import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LADO = 512  # cada una de las cuatro variantes; la imagen entera mide 1024
RESOLUCIONES = {"1k": 1024, "512": 512}

# especie: dibujo, color del haz, color de los nervios, color del borde y la punta, nervios por lado,
#          inclinación de los nervios (en largo de hoja por ancho), rugosidad, semilla
HOJAS = {
    "roble": ("hoja", (0.16, 0.27, 0.08), (0.36, 0.43, 0.18), (0.22, 0.25, 0.08), 7, 0.22, 0.55, 1),
    "haya": ("hoja", (0.20, 0.36, 0.08), (0.42, 0.52, 0.20), (0.24, 0.34, 0.08), 9, 0.30, 0.38, 2),
    "abedul": ("hoja", (0.26, 0.40, 0.10), (0.46, 0.55, 0.24), (0.30, 0.38, 0.10), 6, 0.30, 0.45, 3),
    "sauce_lloron": ("hoja", (0.24, 0.36, 0.15), (0.45, 0.52, 0.32), (0.30, 0.38, 0.18), 14, 0.55, 0.5, 4),
    "olivo": ("hoja", (0.20, 0.27, 0.15), (0.40, 0.44, 0.33), (0.30, 0.33, 0.24), 0, 0.0, 0.6, 5),
    "arbusto": ("hoja", (0.15, 0.30, 0.09), (0.33, 0.45, 0.18), (0.18, 0.28, 0.08), 6, 0.25, 0.45, 6),
    "pino_pinonero": ("aguja", (0.15, 0.27, 0.10), (0.30, 0.40, 0.22), (0.38, 0.32, 0.15), 0, 0.0, 0.5, 7),
    "abeto": ("aguja", (0.07, 0.20, 0.09), (0.28, 0.40, 0.30), (0.10, 0.22, 0.09), 0, 0.0, 0.45, 8),
    "encina": ("hoja", (0.09, 0.16, 0.06), (0.25, 0.30, 0.15), (0.14, 0.17, 0.08), 5, 0.25, 0.32, 10),
    "platano": ("hoja", (0.19, 0.33, 0.09), (0.40, 0.48, 0.20), (0.24, 0.32, 0.10), 5, 0.45, 0.45, 11),
    "chopo": ("hoja", (0.20, 0.36, 0.11), (0.42, 0.52, 0.24), (0.26, 0.36, 0.12), 6, 0.3, 0.35, 12),
    "castano": ("hoja", (0.15, 0.29, 0.08), (0.36, 0.45, 0.18), (0.20, 0.28, 0.08), 16, 0.35, 0.45, 13),
    "arce": ("hoja", (0.20, 0.36, 0.10), (0.40, 0.50, 0.22), (0.24, 0.34, 0.10), 5, 0.5, 0.45, 14),
    "arce_otono": ("hoja", (0.55, 0.16, 0.04), (0.70, 0.40, 0.10), (0.60, 0.32, 0.04), 5, 0.5, 0.5, 15),
    "cipres": ("escama", (0.09, 0.21, 0.08), (0.20, 0.32, 0.12), (0.12, 0.20, 0.07), 0, 0.0, 0.55, 9),
}


def _ruido(azar, celdas, lado=LADO):
    """Ruido suave en [0, 1]: rejilla aleatoria ampliada con interpolación bicúbica."""
    rejilla = (azar.random((celdas, celdas)) * 255).astype(np.uint8)
    imagen = Image.fromarray(rejilla).resize((lado, lado), Image.BICUBIC)
    return np.asarray(imagen, dtype=float) / 255.0


def _fractal(azar, octavas=(4, 9, 20, 48)):
    total, peso = 0.0, 0.0
    for i, celdas in enumerate(octavas):
        w = 0.55 ** i
        total = total + _ruido(azar, celdas) * w
        peso += w
    return total / peso


def _linea(distancia, ancho):
    """1 en la línea y 0 lejos de ella, con borde suave."""
    return np.clip(1.0 - distancia / ancho, 0.0, 1.0) ** 1.5


def _mapas(dibujo, nervios, inclinacion, azar):
    """(nervios 0-1, altura 0-1, borde 0-1) en coordenadas de la hoja."""
    v, u = np.mgrid[0:LADO, 0:LADO] / float(LADO - 1)
    v = 1.0 - v  # la fila 0 de la imagen es la punta (v = 1)
    x = u - 0.5
    borde = np.clip((np.abs(x) - 0.38) / 0.12, 0.0, 1.0)
    detalle = _fractal(azar)
    if dibujo == "hoja":
        central = _linea(np.abs(x), 0.012 + 0.012 * (1.0 - v))
        secundarios = np.zeros_like(u)
        if nervios:
            # Cada nervio sale del central y sube hacia el borde: v = v0 + inclinacion * |x| * 2.
            fase = (v - inclinacion * np.abs(x) * 2.0) * nervios
            distancia = np.abs(fase - np.round(fase)) / nervios
            ancho = 0.006 * (1.0 - np.abs(x) * 1.4)
            secundarios = _linea(distancia, np.maximum(ancho, 0.0015)) * (np.abs(x) > 0.015) * (v > 0.04)
        red = _linea(np.abs(_fractal(azar, (30, 70)) - 0.5), 0.02) * 0.25  # nervaduras finas
        lineas = np.maximum(central, np.maximum(secundarios * 0.8, red))
        altura = 0.6 + 0.25 * np.cos(np.clip(np.abs(x) * 2.0, 0, 1) * np.pi / 2) - 0.35 * lineas + 0.06 * detalle
    elif dibujo == "aguja":
        lineas = _linea(np.abs(x), 0.06) * 0.6 + _linea(np.abs(np.abs(x) - 0.22), 0.04) * 0.5
        altura = np.cos(np.clip(np.abs(x) * 2.0, 0, 1) * np.pi / 2) * 0.8 + 0.05 * detalle
        borde = np.clip((v - 0.85) / 0.15, 0.0, 1.0) * 0.8 + np.clip((0.08 - v) / 0.08, 0.0, 1.0) * 0.6
    else:  # escama: ramita de ciprés hecha de escamas solapadas
        filas = 18
        fila = v * filas + np.abs(x) * 3.0
        dentro = fila - np.floor(fila)
        lineas = _linea(dentro, 0.08) * 0.8
        altura = dentro * 0.7 + 0.2 * np.cos(np.clip(np.abs(x) * 2.0, 0, 1) * np.pi / 2) + 0.05 * detalle
        borde = borde * 0.6
    return np.clip(lineas, 0, 1), np.clip(altura, 0, 1), borde, detalle


def _normal(altura, fuerza):
    """Normal en espacio tangente, estilo OpenGL (verde hacia arriba de la imagen)."""
    dx = (np.roll(altura, -1, axis=1) - np.roll(altura, 1, axis=1)) * 0.5
    dy = (np.roll(altura, 1, axis=0) - np.roll(altura, -1, axis=0)) * 0.5  # hacia arriba de la imagen
    n = np.dstack((-dx * fuerza, -dy * fuerza, np.ones_like(altura)))
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return (n * 0.5 + 0.5) * 255.0


def _srgb(lineal):
    return np.where(lineal <= 0.0031308, lineal * 12.92, 1.055 * np.power(np.clip(lineal, 0, 1), 1 / 2.4) - 0.055)


# Variantes en 2x2 (abajo izquierda, abajo derecha, arriba izquierda, arriba derecha):
# normal, más oscura, más amarilla y algo azulada.
VARIANTES = ((1.0, 1.0, 1.0), (0.7, 0.76, 0.68), (1.25, 1.15, 0.75), (0.85, 0.98, 1.1))


def generar(especie):
    """{canal: imagen 1024x1024} con las cuatro variantes en 2x2."""
    partes = [generar_variante(especie, i) for i in range(4)]
    resultado = {}
    for canal in partes[0]:
        abajo = np.concatenate((partes[0][canal], partes[1][canal]), axis=1)
        arriba = np.concatenate((partes[2][canal], partes[3][canal]), axis=1)
        resultado[canal] = np.concatenate((arriba, abajo), axis=0)  # la fila 0 es v = 1
    return resultado


def generar_variante(especie, variante=0):
    dibujo, haz, nervio, borde_color, nervios, inclinacion, rugosidad, semilla = HOJAS[especie]
    azar = np.random.default_rng(semilla * 10 + variante)
    tono = np.array(VARIANTES[variante])
    lineas, altura, borde, detalle = _mapas(dibujo, nervios, inclinacion, azar)
    v = 1.0 - np.mgrid[0:LADO, 0:LADO][0] / float(LADO - 1)
    manchas = _fractal(azar, (3, 7, 15))
    haz, nervio, borde_color = (np.array(c) for c in (haz, nervio, borde_color))
    color = haz[None, None, :] * (0.82 + 0.36 * manchas[..., None]) * (0.93 + 0.1 * v[..., None])
    color = color * (1 - borde[..., None] * 0.6) + borde_color * borde[..., None] * 0.6
    color = color * (1 - lineas[..., None]) + nervio * lineas[..., None]
    color = color * (0.94 + 0.12 * detalle[..., None]) * 0.8 * tono
    # Al trasluz la hoja se ve más amarilla y clara; los nervios, algo más oscuros.
    trasluz = np.clip(color * np.array((1.9, 1.75, 1.0)) + np.array((0.03, 0.04, 0.0)), 0, 1)
    trasluz = trasluz * (1 - 0.25 * lineas[..., None])
    rugoso = np.clip(rugosidad + 0.12 * lineas + 0.08 * (detalle - 0.5), 0, 1)
    fuerza = {"hoja": 18.0, "aguja": 10.0, "escama": 14.0}[dibujo]
    return {
        "color": (_srgb(color) * 255).round().astype(np.uint8),
        "translucidez": (_srgb(trasluz) * 255).round().astype(np.uint8),
        "normal": _normal(altura, fuerza * LADO / 1024.0).round().astype(np.uint8),  # misma pendiente a cualquier tamaño
        "rugosidad": (rugoso * 255).round().astype(np.uint8),
    }


def guardar(especie, salida):
    mapas = generar(especie)
    rutas = []
    for res, lado in RESOLUCIONES.items():
        carpeta = os.path.join(salida, especie, res)
        os.makedirs(carpeta, exist_ok=True)
        for canal, datos in mapas.items():
            imagen = Image.fromarray(datos)
            if lado != imagen.width:
                imagen = imagen.resize((lado, lado), Image.LANCZOS)
            ruta = os.path.join(carpeta, "hoja_{}.jpg".format(canal))
            imagen.save(ruta, quality=92 if canal != "normal" else 95, optimize=True)
            rutas.append(ruta)
    return rutas


def main(salida=None, *especies):
    salida = os.path.abspath(salida or os.path.join(RAIZ, "texturas"))
    for especie in especies or HOJAS:
        guardar(especie, salida)
        print(especie)
    print("Listo: " + salida)


if __name__ == "__main__":
    main(*sys.argv[1:])
