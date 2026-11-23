"""Estilos de textura «cartoon» y «estilizado» a partir del juego realista (herramienta de desarrollo).

    python3 herramientas/texturas_estilos.py [carpeta texturas] [especie ...]

Lee ``texturas/<especie>/1k/`` y escribe ``texturas/<especie>/<estilo>/1k/`` con los
mismos canales. Solo a 1K: el plugin usa la resolución más cercana que haya, y así
el ZIP para alumnos no crece mucho. Necesita numpy y Pillow.

- Cartoon: colores planos en pocas bandas, más saturados, contorno oscuro en los
  surcos, relieve suave y rugosidad uniforme.
- Estilizado: aspecto de pintura (filtro de Kuwahara), color algo más vivo y el
  relieve suavizado, sin perder la forma de la corteza.

La corteza es repetible: todos los filtros dan la vuelta por los bordes. Las hojas
son un atlas 2x2 de cuatro tonos: cada cuadro se filtra por separado.
"""

import os
import sys

import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESTILOS = ("cartoon", "estilizado")
RESOLUCION = "1k"
CANALES = ("color", "normal", "rugosidad", "translucidez")


# --- filtros (con vuelta por los bordes) ---------------------------------------------------

def _caja(m, radio):
    """Media en una ventana cuadrada de lado 2·radio+1, repetible (np.roll por sumas acumuladas)."""
    if radio <= 0:
        return m.astype(float)
    lado = 2 * radio + 1
    p = np.pad(m.astype(float), [(radio + 1, radio)] * 2 + [(0, 0)] * (m.ndim - 2), mode="wrap")
    s = p.cumsum(0).cumsum(1)
    return (s[lado:, lado:] - s[:-lado, lado:] - s[lado:, :-lado] + s[:-lado, :-lado]) / float(lado * lado)


def suavizar(m, radio, pasadas=3):
    """Aproximación de un desenfoque gaussiano con varias medias de caja."""
    for _ in range(pasadas):
        m = _caja(m, radio)
    return m


def kuwahara(color, radio):
    """Filtro de Kuwahara: cada píxel toma la media del cuadrante (de 4) con menos variación."""
    c = color.astype(float)
    lum = c.mean(axis=2)
    media = _caja(c, radio)
    media_l = _caja(lum, radio)
    var = _caja(lum * lum, radio) - media_l * media_l
    medias, varianzas = [], []
    d = (radio + 1) // 2
    for dy, dx in ((-d, -d), (-d, d), (d, -d), (d, d)):
        medias.append(np.roll(media, (dy, dx), axis=(0, 1)))
        varianzas.append(np.roll(var, (dy, dx), axis=(0, 1)))
    eleccion = np.argmin(np.stack(varianzas), axis=0)
    resultado = np.zeros_like(c)
    for i, m in enumerate(medias):
        resultado += m * (eleccion == i)[..., None]
    return resultado


def _hsv(c):
    c = c / 255.0
    v = c.max(axis=2)
    m = c.min(axis=2)
    s = np.where(v > 1e-6, (v - m) / np.maximum(v, 1e-6), 0.0)
    return v, s


def saturar(c, factor):
    gris = c.mean(axis=2, keepdims=True)
    return gris + (c - gris) * factor


def bandas(c, niveles, suave=0.15):
    """Posteriza el brillo en ``niveles`` bandas conservando el tono (cel shading)."""
    brillo = np.maximum(c.max(axis=2, keepdims=True), 1.0)
    v = brillo / 255.0
    x = v * niveles
    base = np.floor(x)
    f = x - base
    # Paso suave entre bandas para que no salgan dientes de sierra
    paso = np.clip((f - (1 - suave)) / suave, 0, 1)
    nuevo = np.clip((base + paso + 0.5) / niveles, 0.08, 1.0)
    return c / brillo * nuevo * 255.0


def aplanar_normal(n, fuerza, radio):
    """Suaviza el mapa de normales y lo acerca a plano (fuerza 0 = plano, 1 = igual)."""
    v = n.astype(float) / 127.5 - 1.0
    v = suavizar(v, radio) if radio else v
    v[..., :2] *= fuerza
    v[..., 2] = np.sqrt(np.clip(1.0 - v[..., 0] ** 2 - v[..., 1] ** 2, 0.0, 1.0))
    return (v + 1.0) * 127.5


def _contorno(normal, umbral):
    """Máscara de los surcos: donde el relieve cambia mucho (para la línea del cartoon)."""
    v = normal.astype(float) / 127.5 - 1.0
    inclinacion = np.sqrt(v[..., 0] ** 2 + v[..., 1] ** 2)
    inclinacion = suavizar(inclinacion[..., None], 1, 1)[..., 0]
    return np.clip((inclinacion - umbral) / 0.15, 0, 1)


# --- estilos ------------------------------------------------------------------------------

def cartoon(mapas, parte):
    color = mapas["color"].astype(float)
    lado = color.shape[0]
    r = max(1, lado // 256)
    if parte == "corteza":
        color = bandas(saturar(kuwahara(color, 3 * r), 1.35), 4)
    else:
        # Hoja: color casi plano y los nervios como líneas limpias
        liso = suavizar(color, 12 * r)
        nervios = np.clip((color - suavizar(color, 3 * r)).mean(axis=2, keepdims=True) - 4.0, 0, None)
        nervios = np.clip(nervios / 10.0, 0, 1)
        color = saturar(liso, 1.3) * (1 + 0.35 * nervios)
    resultado = {}
    if "normal" in mapas:
        if parte == "corteza":
            linea = _contorno(mapas["normal"], 0.45)
            color = color * (1 - 0.55 * linea[..., None])
        resultado["normal"] = aplanar_normal(mapas["normal"], 0.35, 2 * r)
    resultado["color"] = color
    if "rugosidad" in mapas:
        resultado["rugosidad"] = np.full_like(mapas["rugosidad"], 200.0, dtype=float)
    if "translucidez" in mapas:
        resultado["translucidez"] = saturar(suavizar(mapas["translucidez"].astype(float), 12 * r), 1.3)
    return resultado


def estilizado(mapas, parte):
    color = mapas["color"].astype(float)
    lado = color.shape[0]
    r = max(1, lado // 256)
    if parte == "corteza":
        color = kuwahara(kuwahara(color, 2 * r), r)
    else:
        color = kuwahara(kuwahara(color, 4 * r), 2 * r)
    color = saturar(color, 1.2)
    # Un poco más de contraste local, como pinceladas
    detalle = color - suavizar(color, 6 * r, 2)
    color = color + 0.35 * detalle
    resultado = {"color": color}
    if "normal" in mapas:
        resultado["normal"] = aplanar_normal(mapas["normal"], 0.7, r)
    if "rugosidad" in mapas:
        resultado["rugosidad"] = suavizar(mapas["rugosidad"].astype(float), 2 * r)
    if "translucidez" in mapas:
        resultado["translucidez"] = saturar(kuwahara(mapas["translucidez"].astype(float), 4 * r), 1.15)
    return resultado


FILTROS = {"cartoon": cartoon, "estilizado": estilizado}


# --- lectura y escritura -------------------------------------------------------------------

def _leer(ruta):
    im = Image.open(ruta)
    return np.asarray(im.convert("RGB"), dtype=float)


def _guardar(m, ruta):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    Image.fromarray(np.clip(m, 0, 255).astype(np.uint8)).save(ruta, quality=92, subsampling=0)


def _por_cuadros(funcion, mapas, parte):
    """Atlas 2x2 de hojas: filtra cada cuadro por separado (sin mezclar tonos vecinos)."""
    lado = next(iter(mapas.values())).shape[0]
    mitad = lado // 2
    salida = {}
    for fy in (0, mitad):
        for fx in (0, mitad):
            trozo = {c: m[fy:fy + mitad, fx:fx + mitad] for c, m in mapas.items()}
            for canal, m in funcion(trozo, parte).items():
                salida.setdefault(canal, np.zeros((lado, lado, 3)))[fy:fy + mitad, fx:fx + mitad] = m
    return salida


def generar(carpeta, especie, estilos=ESTILOS):
    origen = os.path.join(carpeta, especie, RESOLUCION)
    hechos = []
    for parte in ("corteza", "hoja"):
        mapas = {}
        for canal in CANALES:
            ruta = os.path.join(origen, "{}_{}.jpg".format(parte, canal))
            if os.path.isfile(ruta):
                mapas[canal] = _leer(ruta)
        if "color" not in mapas:
            continue
        for estilo in estilos:
            funcion = FILTROS[estilo]
            resultado = funcion(mapas, parte) if parte == "corteza" else _por_cuadros(funcion, mapas, parte)
            for canal, m in resultado.items():
                destino = os.path.join(carpeta, especie, estilo, RESOLUCION, "{}_{}.jpg".format(parte, canal))
                _guardar(m, destino)
                hechos.append(destino)
    return hechos


def especies(carpeta):
    return sorted(d for d in os.listdir(carpeta)
                  if os.path.isdir(os.path.join(carpeta, d, RESOLUCION)))


def main(carpeta=None, *nombres):
    carpeta = os.path.abspath(carpeta or os.path.join(RAIZ, "texturas"))
    for especie in nombres or especies(carpeta):
        print(especie, len(generar(carpeta, especie)))


if __name__ == "__main__":
    main(*sys.argv[1:])
