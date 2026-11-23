"""Genera las texturas de corteza de cada especie con Substance Designer (sbsrender).

Se ejecuta con mayapy (trae numpy y PySide6), en un ordenador con Substance 3D
Designer instalado. No abre ninguna aplicación de Substance::

    mayapy herramientas/texturas_corteza.py <carpeta de salida> [--4k] [especie ...]
    mayapy herramientas/texturas_corteza.py --catalogo <carpeta>   (para elegir el dibujo de cada especie)

Parte de materiales de corteza de serie (``wood_bark`` y ``stylized_wood_bark``
de Substance 3D Painter, ``bark`` de Sampler) con unos ajustes por especie,
retoca el resultado con numpy (relieve, contraste, lenticelas del abedul) y
deja en la salida, junto con una hoja de contacto::

    <especie>/<512|1k|2k|4k>/corteza_color.jpg, corteza_normal.jpg, corteza_rugosidad.jpg

La normal se deja al estilo OpenGL (verde hacia arriba), que es lo que espera
Maya: si Substance la da al estilo DirectX, se le da la vuelta al verde.
"""

import glob
import os
import shutil
import subprocess
import sys
import tempfile

SBSRENDER = (
    "/Applications/Adobe Substance 3D Designer/Adobe Substance 3D Designer.app/Contents/MacOS/sbsrender",
    r"C:\Program Files\Adobe\Adobe Substance 3D Designer\sbsrender.exe",
)
_PINTOR = "/Applications/Adobe Substance 3D Painter/Adobe Substance 3D Painter.app/Contents/Resources/starter_assets/"
_PINTOR_WIN = "C:\\Program Files\\Adobe\\Adobe Substance 3D Painter\\resources\\starter_assets\\"
# Materiales de partida: rutas fijas o patrones de búsqueda
FUENTES = {
    "wood_bark": (_PINTOR + "materials/Wood/wood_bark.sbsar", _PINTOR_WIN + r"materials\Wood\wood_bark.sbsar"),
    "stylized_wood_bark": (_PINTOR + "materials/Wood/stylized_wood_bark.sbsar",
                           _PINTOR_WIN + r"materials\Wood\stylized_wood_bark.sbsar"),
    "bark": ("/Applications/Adobe Substance 3D Sampler*/**/bark.sbsar",
             r"C:\Program Files\Adobe\Adobe Substance 3D Sampler*\**\bark.sbsar"),
}
# Las salidas cambian de nombre según el material
SALIDAS = {
    "color": ("basecolor", "base_color"),
    "normal": ("normal",),
    "rugosidad": ("roughness", "specular_roughness"),
    "altura": ("height",),
}
TAMANOS = {"512": 512, "1k": 1024, "2k": 2048, "4k": 4096}

# Por especie:
#   fuente, preset y valores: material de partida, preset (o None) y entradas del .sbsar
#   (en los estilizados, fake_lighting a 0: si no, traen luz pintada que en Arnold se ve doble);
#   relieve: multiplica la inclinación de la normal (menos de 1 = más lisa);
#   contraste: del color respecto a su media (menos de 1 = más uniforme);
#   repetir: n x n copias en la imagen (dibujo más menudo);
#   tinte: color medio (sRGB, 0-1) al que se lleva el color; saturacion: menos de 1 = más gris;
#   lenticelas: trazos oscuros horizontales (abedul); manchas: placas claras y verdosas (plátano).
CORTEZAS = {
    "roble": dict(fuente="wood_bark", preset=None, valores={
        "$randomseed": 7, "bark_color": (0.33, 0.30, 0.26), "bark_roughness": 0.9, "bark_density": 0.8,
        "missing_part_density": 0.3, "normal_intensity": 1.2}),
    "haya": dict(fuente="wood_bark", preset="Small Wood Bark", valores={
        "$randomseed": 3, "bark_color": (0.56, 0.56, 0.53), "bark_roughness": 0.1, "bark_density": 0.15,
        "missing_part_density": 0.0}, relieve=0.15, contraste=0.35),
    "pino_pinonero": dict(fuente="stylized_wood_bark", preset=None, valores={
        "$randomseed": 11, "fake_lighting": 0, "bark_vertical_deformation": 0, "bark_horizontal_deformation": 0},
        tinte=(0.46, 0.29, 0.19)),
    "abeto": dict(fuente="wood_bark", preset="Small Wood Bark", valores={
        "$randomseed": 5, "bark_color": (0.37, 0.33, 0.29), "bark_roughness": 0.4, "bark_density": 0.4,
        "missing_part_density": 0.1}),
    "abedul": dict(fuente="wood_bark", preset="Small Wood Bark", valores={
        "$randomseed": 9, "bark_color": (0.86, 0.84, 0.79), "bark_roughness": 0.2, "bark_density": 0.25,
        "missing_part_density": 0.0}, relieve=0.2, contraste=0.3, lenticelas=True),
    # Solo color y relieve: si se tocan densidad o rugosidad, se pierden los surcos largos del preset.
    "sauce_lloron": dict(fuente="wood_bark", preset="Long Wood Bark", valores={
        "$randomseed": 13, "bark_color": (0.36, 0.32, 0.27), "normal_intensity": 1.2}),
    "cipres": dict(fuente="stylized_wood_bark", preset="Burnt Bark", valores={
        "$randomseed": 17, "fake_lighting": 0, "bark_horizontal_deformation": 0.5}, tinte=(0.43, 0.31, 0.23), saturacion=0.8),
    "olivo": dict(fuente="stylized_wood_bark", preset="Mossy Bark", valores={
        "$randomseed": 19, "fake_lighting": 0, "bark_horizontal_deformation": 1}, tinte=(0.41, 0.39, 0.35), saturacion=0.35),
    "arbusto": dict(fuente="wood_bark", preset="Small Wood Bark", valores={
        "$randomseed": 23, "bark_color": (0.34, 0.29, 0.24), "bark_roughness": 0.4, "bark_density": 0.4,
        "missing_part_density": 0.1}, repetir=2),
    "encina": dict(fuente="wood_bark", preset="Small Wood Bark", valores={
        "$randomseed": 29, "bark_color": (0.28, 0.26, 0.24), "normal_intensity": 1.2}),
    "platano": dict(fuente="wood_bark", preset="Small Wood Bark", valores={
        "$randomseed": 31, "bark_color": (0.55, 0.53, 0.45)}, relieve=0.25, contraste=0.4, manchas=True),
    "chopo": dict(fuente="wood_bark", preset="Small Wood Bark", valores={
        "$randomseed": 37, "bark_color": (0.60, 0.60, 0.54)}, relieve=0.35, contraste=0.5),
    "castano": dict(fuente="wood_bark", preset="Long Wood Bark", valores={
        "$randomseed": 41, "bark_color": (0.36, 0.30, 0.25), "normal_intensity": 1.2}),
    "arce": dict(fuente="wood_bark", preset="Small Wood Bark", valores={
        "$randomseed": 43, "bark_color": (0.42, 0.38, 0.33)}, relieve=0.6),
}
CORTEZAS["arce_otono"] = CORTEZAS["arce"]

# Para --catalogo: (fuente, preset) con sus valores por defecto, para elegir el dibujo de cada especie
VARIANTES = [(f, p) for f, ps in (
    ("wood_bark", (None, "Wet Wood Bark", "Long Wood Bark", "Small Wood Bark")),
    ("bark", (None, "Wet Bark", "Long Bark", "Small Bark")),
    ("stylized_wood_bark", (None, "Coconut Tree", "Mossy Bark", "Burnt Bark")),
) for p in ps]


def _primero(rutas):
    for r in rutas:
        encontrados = sorted(glob.glob(r, recursive=True)) if "*" in r else ([r] if os.path.exists(r) else [])
        if encontrados:
            return encontrados[0]
    raise SystemExit("No encuentro: " + rutas[0])


def _texto(valor):
    if isinstance(valor, (tuple, list)):
        return ",".join("{:.3f}".format(x) for x in valor)
    return str(valor)


def renderizar(fuente, preset, valores, carpeta, tamano_log2=11):
    """Renderiza el .sbsar y devuelve {canal: ruta png} con los canales que haya dado."""
    orden = [_primero(SBSRENDER), "render", _primero(FUENTES[fuente]),
             "--output-path", carpeta, "--output-name", "{outputNodeName}", "--output-format", "png",
             "--set-value", "$outputsize@{0},{0}".format(tamano_log2)]
    for clave, valor in valores.items():
        orden += ["--set-value", "{}@{}".format(clave, _texto(valor))]
    for nombres in SALIDAS.values():
        for nombre in nombres:
            orden += ["--input-graph-output", nombre]
    if preset:
        orden += ["--use-preset", preset]
    subprocess.check_call(orden)
    resultado = {}
    for canal, nombres in SALIDAS.items():
        for nombre in nombres:
            ruta = os.path.join(carpeta, nombre + ".png")
            if os.path.exists(ruta):
                resultado[canal] = ruta
                break
    return resultado


def _qt():
    from PySide6 import QtGui
    if QtGui.QGuiApplication.instance() is None:
        QtGui.QGuiApplication(["texturas", "-platform", "offscreen"])
    return QtGui


def _a_numpy(imagen):
    import numpy as np
    QtGui = _qt()
    imagen = imagen.convertToFormat(QtGui.QImage.Format_RGB888)
    ancho, alto = imagen.width(), imagen.height()
    datos = np.frombuffer(imagen.constBits(), np.uint8, imagen.bytesPerLine() * alto)
    return datos.reshape(alto, imagen.bytesPerLine())[:, :ancho * 3].reshape(alto, ancho, 3).copy()


def _de_numpy(matriz):
    QtGui = _qt()
    alto, ancho = matriz.shape[:2]
    matriz = matriz.astype("uint8").copy(order="C")
    return QtGui.QImage(matriz.data, ancho, alto, ancho * 3, QtGui.QImage.Format_RGB888).copy()


def normal_es_directx(normal, altura):
    """True si la normal está al estilo DirectX (verde hacia abajo).

    Normal = (-dh/dx, -dh/dy, 1): en OpenGL, donde la superficie sube hacia
    arriba de la imagen el verde baja de 0,5; en DirectX, sube.
    """
    import numpy as np
    n = _a_numpy(normal)[:, :, 1].astype(float) - 127.5
    h = _a_numpy(altura)[:, :, 0].astype(float)
    pendiente = np.roll(h, 1, axis=0) - np.roll(h, -1, axis=0)  # sube hacia la fila de arriba
    return float((n * pendiente).sum()) > 0


def _trazo(filas, columnas, y, x, largo, grueso, alto, ancho, azar):
    """Elipse alargada de borde nítido y algo irregular, repetible por los bordes."""
    import numpy as np
    dy = (filas - y + alto / 2.0) % alto - alto / 2.0
    dx = (columnas - x + ancho / 2.0) % ancho - ancho / 2.0
    ondula = 1.0 + 0.35 * np.sin(dx / max(largo, 1.0) * azar.uniform(6, 14) + azar.uniform(0, 6.3))
    forma = 1.0 - (dx / (largo / 2.0)) ** 2 - (dy / (grueso * ondula)) ** 2
    return np.clip(forma * 6.0, 0.0, 1.0) * azar.uniform(0.75, 1.0)


def _lenticelas(color, normal, rugosidad, semilla):
    """Trazos oscuros horizontales del abedul (repetibles: se dan la vuelta por los bordes)."""
    import numpy as np
    azar = np.random.default_rng(semilla)
    alto, ancho = color.shape[:2]
    filas = np.arange(alto)[:, None]
    columnas = np.arange(ancho)[None, :]
    marca = np.zeros((alto, ancho))
    # Trazos finos y nítidos de largo muy variable, por bandas, y alguna mancha grande suelta.
    for _ in range(int(40 * ancho / 1024.0)):
        y, x = azar.uniform(0, alto), azar.uniform(0, ancho)
        largo = ancho * azar.choice((azar.uniform(0.02, 0.08), azar.uniform(0.08, 0.35)), p=(0.6, 0.4))
        grueso = azar.uniform(0.0012, 0.004) * alto
        marca = np.maximum(marca, _trazo(filas, columnas, y, x, largo, grueso, alto, ancho, azar))
    for _ in range(int(2 * ancho / 1024.0)):
        y, x = azar.uniform(0, alto), azar.uniform(0, ancho)
        marca = np.maximum(marca, _trazo(filas, columnas, y, x, ancho * azar.uniform(0.12, 0.3),
                                         alto * azar.uniform(0.006, 0.014), alto, ancho, azar))
    oscuro = np.array((38.0, 34.0, 32.0))
    color[:] = color * (1 - marca[..., None]) + oscuro * marca[..., None]
    rugosidad[:] = np.clip(rugosidad + marca[..., None] * 60.0, 0, 255)
    # Un poco hundidas: la normal se inclina en el borde de cada marca.
    gy = np.roll(marca, 1, axis=0) - np.roll(marca, -1, axis=0)
    normal[:, :, 1] = np.clip(normal[:, :, 1] + gy * 40.0, 0, 255)


def _manchas(color, normal, semilla):
    """Placas del plátano de sombra: manchas grandes crema, oliva y gris, más lisas (repetibles)."""
    import numpy as np
    azar = np.random.default_rng(semilla)
    alto, ancho = color.shape[:2]
    resultado = color.copy()
    tonos = (np.array((205.0, 196.0, 160.0)), np.array((150.0, 152.0, 110.0)), np.array((120.0, 115.0, 100.0)))
    filas = np.arange(alto)[:, None]
    columnas = np.arange(ancho)[None, :]
    for tono in tonos:
        # Suma de manchas gaussianas repetibles (distancias que dan la vuelta) y un umbral: placas irregulares
        campo = np.zeros((alto, ancho))
        for _ in range(26):
            cy, cx = azar.uniform(0, alto), azar.uniform(0, ancho)
            ry, rx = alto * azar.uniform(0.03, 0.09), ancho * azar.uniform(0.03, 0.09)
            dy = (filas - cy + alto / 2.0) % alto - alto / 2.0
            dx = (columnas - cx + ancho / 2.0) % ancho - ancho / 2.0
            campo += np.exp(-(dx / rx) ** 2 - (dy / ry) ** 2)
        mascara = np.clip((campo - 0.55) * 6.0, 0, 1)[..., None]
        resultado = resultado * (1 - mascara) + tono * mascara
        normal[:] = normal * (1 - mascara * 0.8) + np.array((127.5, 127.5, 255.0)) * mascara * 0.8
    color[:] = resultado


def retocar(mapas, ajustes, semilla=0):
    """Aplica relieve, contraste, repetición y lenticelas a {canal: matriz numpy}."""
    import numpy as np
    color = mapas["color"].astype(float)
    normal = mapas["normal"].astype(float)
    rugosidad = mapas["rugosidad"].astype(float)
    saturacion = ajustes.get("saturacion", 1.0)
    if saturacion != 1.0:
        gris = color.mean(axis=2, keepdims=True)
        color = gris + (color - gris) * saturacion
    if ajustes.get("tinte"):
        media = color.reshape(-1, 3).mean(axis=0)
        color = color * (np.array(ajustes["tinte"]) * 255.0 / np.maximum(media, 1.0))
    contraste = ajustes.get("contraste", 1.0)
    if contraste != 1.0:
        media = color.reshape(-1, 3).mean(axis=0)
        color = media + (color - media) * contraste
    relieve = ajustes.get("relieve", 1.0)
    if relieve != 1.0:
        n = normal / 127.5 - 1.0
        n[:, :, :2] *= relieve
        n /= np.maximum(np.linalg.norm(n, axis=2, keepdims=True), 1e-6)
        normal = (n + 1.0) * 127.5
    if ajustes.get("lenticelas"):
        _lenticelas(color, normal, rugosidad, semilla)
    if ajustes.get("manchas"):
        _manchas(color, normal, semilla)
    repetir = ajustes.get("repetir", 1)
    resultado = {"color": color, "normal": normal, "rugosidad": rugosidad}
    for canal, m in resultado.items():
        m = np.clip(m, 0, 255).astype(np.uint8)
        if repetir > 1:
            m = np.tile(m, (repetir, repetir, 1))
        resultado[canal] = m
    return resultado


def guardar(imagenes, destino, resoluciones, ajustes=None, semilla=0):
    QtGui = _qt()
    from PySide6 import QtCore
    voltear = normal_es_directx(QtGui.QImage(imagenes["normal"]), QtGui.QImage(imagenes["altura"]))
    mapas = {canal: _a_numpy(QtGui.QImage(imagenes[canal])) for canal in ("color", "normal", "rugosidad")}
    if voltear:
        mapas["normal"][:, :, 1] = 255 - mapas["normal"][:, :, 1]
    mapas = retocar(mapas, ajustes or {}, semilla)
    for canal, matriz in mapas.items():
        imagen = _de_numpy(matriz)
        if canal == "rugosidad":
            imagen = imagen.convertToFormat(QtGui.QImage.Format_Grayscale8)
        for res in resoluciones:
            lado = TAMANOS[res]
            copia = imagen if imagen.width() == lado else imagen.scaled(
                lado, lado, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
            carpeta = os.path.join(destino, res)
            os.makedirs(carpeta, exist_ok=True)
            copia.save(os.path.join(carpeta, "corteza_{}.jpg".format(canal)), "JPG", 92)
    return voltear


def hoja_de_contacto(filas, ruta, lado=384):
    """filas: [(título, [rutas de imagen])]. Cada imagen va en mosaico 2x2 reducida a ``lado``."""
    QtGui = _qt()
    from PySide6 import QtCore
    columnas = max(len(f[1]) for f in filas)
    hoja = QtGui.QImage(columnas * lado, len(filas) * (lado + 22), QtGui.QImage.Format_RGB888)
    hoja.fill(QtGui.QColor(255, 255, 255))
    pintor = QtGui.QPainter(hoja)
    for i, (titulo, rutas) in enumerate(filas):
        for j, r in enumerate(rutas):
            imagen = QtGui.QImage(r).scaled(lado // 2, lado // 2, QtCore.Qt.IgnoreAspectRatio,
                                             QtCore.Qt.SmoothTransformation)
            for a in range(2):
                for b in range(2):
                    pintor.drawImage(j * lado + a * lado // 2, i * (lado + 22) + b * lado // 2, imagen)
        pintor.setPen(QtGui.QColor(0, 0, 0))
        pintor.drawText(6, i * (lado + 22) + lado + 16, titulo)
    pintor.end()
    hoja.save(ruta)
    return ruta


def catalogo(salida):
    """Renderiza a 1K cada variante de VARIANTES y monta una hoja de contacto (color y normal)."""
    filas = []
    for fuente, preset in VARIANTES:
        nombre = "{}__{}".format(fuente, (preset or "defecto").replace(" ", "_"))
        carpeta = os.path.join(salida, nombre)
        os.makedirs(carpeta, exist_ok=True)
        try:
            imagenes = renderizar(fuente, preset, {}, carpeta, 10)
        except (subprocess.CalledProcessError, SystemExit) as error:
            print("{}: FALLA ({})".format(nombre, error))
            continue
        filas.append((nombre, [imagenes[c] for c in ("color", "normal") if c in imagenes]))
        print("{}: {}".format(nombre, ", ".join(sorted(imagenes))))
    print(hoja_de_contacto(filas, os.path.join(salida, "catalogo_cortezas.png")))


def main(argumentos):
    if argumentos[:1] == ["--catalogo"]:
        return catalogo(os.path.abspath(argumentos[1]))
    con_4k = "--4k" in argumentos
    argumentos = [a for a in argumentos if a != "--4k"]
    if not argumentos:
        raise SystemExit(__doc__)
    salida = os.path.abspath(argumentos[0])
    especies = argumentos[1:] or list(CORTEZAS)
    resoluciones = ["512", "1k", "2k"] + (["4k"] if con_4k else [])
    filas = []
    for especie in especies:
        ajustes = CORTEZAS[especie]
        temporal = tempfile.mkdtemp(prefix="arboles_corteza_")
        try:
            repetir = ajustes.get("repetir", 1)
            tamano = (12 if con_4k else 11) - (1 if repetir > 1 else 0)
            imagenes = renderizar(ajustes["fuente"], ajustes.get("preset"), ajustes.get("valores", {}),
                                  temporal, tamano)
            semilla = ajustes.get("valores", {}).get("$randomseed", 0)
            voltear = guardar(imagenes, os.path.join(salida, especie), resoluciones, ajustes, semilla)
            print("{}: {}{}".format(especie, ", ".join(resoluciones), " (verde de la normal volteado)" if voltear else ""))
        finally:
            shutil.rmtree(temporal, ignore_errors=True)
        filas.append((especie, [os.path.join(salida, especie, "1k", "corteza_{}.jpg".format(c))
                                for c in ("color", "normal")]))
    print(hoja_de_contacto(filas, os.path.join(salida, "hoja_cortezas.png")))
    print("Listo: " + salida)


if __name__ == "__main__":
    main(sys.argv[1:])
